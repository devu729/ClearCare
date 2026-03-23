"""
Agent 1: Policy Parser
PDF → text extraction → PHI stripping → chunking →
Gemini embeddings (free API, no PyTorch, no local model) → ChromaDB.
"""

import fitz
import chromadb
import hashlib
import re
import logging
import google.generativeai as genai
from config import get_settings
from security.phi_stripper import strip_phi_from_chunks

logger = logging.getLogger(__name__)

_RULE_SIGNALS = [
    r"\b(section|rule|article|clause|policy|coverage|benefit|exclusion|limitation)\b",
    r"\b(prior authorization|pre-authorization|medical necessity|not covered|covered)\b",
    r"\b(must|shall|required|eligible|ineligible|applies|does not apply)\b",
    r"\b\d+\.\d+",
    r"\$[\d,]+",
    r"\b\d+\s*(days?|months?|years?)\b",
]


def _embed(texts: list[str]) -> list[list[float]]:
    """
    Gemini free embedding API.
    No PyTorch. No local model. No 2GB downloads.
    Runs in the cloud — works on any free tier server.
    """
    s = get_settings()
    genai.configure(api_key=s.gemini_api_key)
    result = genai.embed_content(
        model  =  "text-embedding-004",
        content = texts,
        task_type = "RETRIEVAL_DOCUMENT",
    )
    return result["embedding"] if len(texts) == 1 else [r for r in result["embedding"]]


def _chroma():
    s = get_settings()
    client = chromadb.PersistentClient(path=s.chroma_persist_path)
    return client.get_or_create_collection(
        name     = "policy_rules",
        metadata = {"hnsw:space": "cosine"},
    )


def _extract_pages(pdf_bytes: bytes) -> list[dict]:
    pages = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for i in range(len(doc)):
        text = doc[i].get_text("text").strip()
        if text:
            pages.append({"page_num": i + 1, "text": text})
    doc.close()
    return pages


def _chunk(pages: list[dict], size: int = 800, overlap: int = 100) -> list[dict]:
    chunks = []
    for page in pages:
        words = page["text"].split()
        cur, cur_len = [], 0
        for w in words:
            cur.append(w)
            cur_len += len(w) + 1
            if cur_len >= size:
                chunks.append({"text": " ".join(cur), "page_num": page["page_num"]})
                cur = cur[-max(1, overlap // 6):]
                cur_len = sum(len(x) + 1 for x in cur)
        if cur:
            chunks.append({"text": " ".join(cur), "page_num": page["page_num"]})
    return chunks


def _is_rule(text: str) -> bool:
    t = text.lower()
    return sum(1 for p in _RULE_SIGNALS if re.search(p, t)) >= 2


def _embed_batch(texts: list[str], batch_size: int = 20) -> list[list[float]]:
    """Embed in batches to respect Gemini API limits."""
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            s = get_settings()
            genai.configure(api_key=s.gemini_api_key)
            result = genai.embed_content(
                model     = "models/text-embedding-004",
                content   = batch,
                task_type = "RETRIEVAL_DOCUMENT",
            )
            embeddings = result["embedding"]
            # Handle both single and batch responses
            if isinstance(embeddings[0], float):
                all_embeddings.append(embeddings)
            else:
                all_embeddings.extend(embeddings)
        except Exception as e:
            logger.error(f"Embedding batch {i} failed: {e}")
            raise
    return all_embeddings


async def parse_policy_pdf(pdf_bytes: bytes, document_name: str, user_id: str) -> dict:
    doc_id = hashlib.sha256(
        f"{user_id}:{document_name}:{len(pdf_bytes)}".encode()
    ).hexdigest()[:16]

    try:
        pages = _extract_pages(pdf_bytes)
        if not pages:
            return {"status": "error", "message": "No text found. Is this a scanned PDF?"}

        chunks = _chunk(pages)
        clean  = strip_phi_from_chunks([c["text"] for c in chunks])

        rule_chunks = [
            {"text": clean[i], "page_num": chunks[i]["page_num"]}
            for i in range(len(chunks)) if _is_rule(clean[i])
        ] or [
            {"text": clean[i], "page_num": chunks[i]["page_num"]}
            for i in range(min(50, len(chunks)))
        ]

        texts = [c["text"] for c in rule_chunks]
        embs  = _embed_batch(texts)

        col = _chroma()
        col.upsert(
            ids        = [f"{doc_id}_{i}" for i in range(len(rule_chunks))],
            embeddings = embs,
            documents  = texts,
            metadatas  = [{
                "document_id":   doc_id,
                "document_name": document_name,
                "page_num":      str(c["page_num"]),
                "user_id":       user_id,
            } for c in rule_chunks],
        )

        return {
            "document_id":   doc_id,
            "document_name": document_name,
            "total_pages":   len(pages),
            "total_chunks":  len(chunks),
            "rule_chunks":   len(rule_chunks),
            "sample_rules":  texts[:3],
            "status":        "success",
            "message":       f"Indexed {len(rule_chunks)} decision rules from {len(pages)} pages.",
        }
    except Exception as e:
        logger.error(f"parse_policy_pdf failed: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


def query_rules(query: str, document_id: str | None = None, n: int = 5) -> list[dict]:
    """Query ChromaDB using Gemini embeddings."""
    s = get_settings()
    genai.configure(api_key=s.gemini_api_key)

    result = genai.embed_content(
        model     = "models/text-embedding-004",
        content   = query,
        task_type = "RETRIEVAL_QUERY",
    )
    query_embedding = result["embedding"]

    col   = _chroma()
    where = {"document_id": document_id} if document_id else None
    res   = col.query(
        query_embeddings = [query_embedding],
        n_results        = n,
        where            = where,
        include          = ["documents", "metadatas", "distances"],
    )

    out = []
    if res["documents"] and res["documents"][0]:
        for i, doc in enumerate(res["documents"][0]):
            out.append({
                "text":          doc,
                "page_num":      res["metadatas"][0][i].get("page_num", "?"),
                "document_name": res["metadatas"][0][i].get("document_name", ""),
                "document_id":   res["metadatas"][0][i].get("document_id", ""),
                "distance":      res["distances"][0][i],
            })
    return out


def list_docs(user_id: str) -> list[dict]:
    try:
        col  = _chroma()
        res  = col.get(where={"user_id": user_id}, include=["metadatas"])
        seen = {}
        for m in res.get("metadatas", []):
            did = m.get("document_id")
            if did and did not in seen:
                seen[did] = {
                    "document_id":   did,
                    "document_name": m.get("document_name", "Unknown"),
                }
        return list(seen.values())
    except Exception:
        return []