"""
Observability Layer — Langfuse
==============================
Traces every AI agent call with:
- Input query (PHI-stripped)
- ChromaDB retrieval results
- Gemini prompt + response
- Token count + latency
- Confidence score
- Errors

Free at https://cloud.langfuse.com
Add to .env:
  LANGFUSE_PUBLIC_KEY=pk-lf-...
  LANGFUSE_SECRET_KEY=sk-lf-...

If keys not set → observability is silently disabled.
App works exactly the same without it.
"""

import logging
import os
from functools import wraps
from config import get_settings

logger = logging.getLogger(__name__)

_langfuse_client = None


def get_langfuse():
    """Get Langfuse client. Returns None if not configured — app still works."""
    global _langfuse_client
    if _langfuse_client is not None:
        return _langfuse_client

    s = get_settings()
    if not s.observability_enabled:
        return None

    try:
        from langfuse import Langfuse
        _langfuse_client = Langfuse(
            public_key=s.langfuse_public_key,
            secret_key=s.langfuse_secret_key,
            host=s.langfuse_host,
        )
        logger.info("Langfuse observability initialized")
        return _langfuse_client
    except Exception as e:
        logger.warning(f"Langfuse init failed (non-critical): {e}")
        return None


def trace_agent_call(name: str):
    """
    Decorator that traces any async agent function in Langfuse.

    Usage:
        @trace_agent_call("denial_tracer")
        async def trace_denial(query: str, ...) -> dict:
            ...

    If Langfuse is not configured, the function runs normally.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            lf = get_langfuse()

            if not lf:
                # Langfuse not configured — just run the function
                return await func(*args, **kwargs)

            # Start a trace
            trace = lf.trace(
                name=name,
                input={
                    "args":   str(args)[:500],
                    "kwargs": {k: str(v)[:200] for k, v in kwargs.items()},
                },
                tags=["clearcare", "production"],
            )

            try:
                result = await func(*args, **kwargs)

                # Log success metadata
                trace.update(
                    output={
                        "status":     result.get("status", "unknown") if isinstance(result, dict) else "ok",
                        "confidence": result.get("confidence") if isinstance(result, dict) else None,
                        "verified":   result.get("verified") if isinstance(result, dict) else None,
                    },
                    level="DEFAULT",
                )
                return result

            except Exception as e:
                # Log failure
                trace.update(
                    output={"error": str(e)},
                    level="ERROR",
                )
                raise

        return wrapper
    return decorator


def log_gemini_call(trace, prompt: str, response_text: str, model: str = "gemini-2.5-flash"):
    """Log a Gemini LLM call as a generation span inside a trace."""
    lf = get_langfuse()
    if not lf or not trace:
        return

    try:
        trace.generation(
            name=f"gemini_{model}",
            model=model,
            input=prompt[:1000],
            output=response_text[:1000],
            usage={
                "input":  len(prompt.split()),
                "output": len(response_text.split()),
                "unit":   "TOKENS",
            },
        )
    except Exception as e:
        logger.debug(f"Langfuse generation log failed (non-critical): {e}")


def log_retrieval(trace, query: str, chunks: list, collection: str = "policy_rules"):
    """Log a ChromaDB retrieval as a span inside a trace."""
    lf = get_langfuse()
    if not lf or not trace:
        return

    try:
        trace.span(
            name="chromadb_retrieval",
            input={"query": query[:200], "collection": collection},
            output={
                "chunks_retrieved": len(chunks),
                "top_distance":     chunks[0]["distance"] if chunks else None,
                "documents":        [c["document_name"] for c in chunks[:3]],
            },
        )
    except Exception as e:
        logger.debug(f"Langfuse retrieval log failed (non-critical): {e}")