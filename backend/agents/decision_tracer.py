"""
Agent 2: Decision Tracer + Dual Explainer + Hallucination Guard
Powered by Google Gemini (free, no credit card needed).

1. Search ChromaDB for policy rules matching the denial
2. Send anonymized context to Gemini → dual explanation
3. Hallucination guard: verify claims against source
4. Return confidence score, source citation, verified flag
"""

import json
import logging
import re
import google.generativeai as genai
from config import get_settings
from security.phi_stripper import strip_phi
from agents.policy_parser import query_rules

logger = logging.getLogger(__name__)

_SYSTEM_TRACER = """You are ClearCare, a healthcare decision intelligence assistant.
You receive insurance policy rule excerpts and a denial reason.
You generate two explanations — one for a clinician, one for a patient.

CRITICAL RULES:
- Only make claims directly supported by the provided policy rule text
- Never invent rule numbers, dollar amounts, or deadlines not in the source
- If something is unclear, say so explicitly
- Patient explanation: plain English, no jargon, empathetic tone
- Clinician explanation: precise, cite rule text, actionable next steps

Respond ONLY with valid JSON — no markdown, no code fences, no preamble:
{
  "clinician_explanation": "2-4 paragraphs, clinical language, rule citations",
  "patient_explanation": "2-4 paragraphs, plain English, empathetic tone",
  "clinician_actions": ["action 1", "action 2", "action 3"],
  "patient_actions": ["step 1", "step 2", "step 3"],
  "source_rule": "e.g. Section 4.2.1 — Prior Authorization Requirements",
  "appeal_deadline": "e.g. 30 days from denial date OR null if unknown",
  "confidence_reasoning": "1-2 sentences explaining confidence level"
}"""

# Separate system instruction for appeal letter
# Explicitly tells Gemini to return ONLY plain text, never JSON
_SYSTEM_APPEAL = """You are a healthcare appeal letter writer.
You write formal, professional insurance appeal letters.
CRITICAL: Return ONLY the letter text as plain text.
Do NOT return JSON. Do NOT use markdown. Do NOT add any explanation before or after the letter.
Start the letter directly. End with the signature."""


def _get_gemini():
    s = get_settings()
    genai.configure(api_key=s.gemini_api_key)
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=_SYSTEM_TRACER,
    )


def _get_gemini_appeal():
    """Separate Gemini instance with appeal-specific system instruction."""
    s = get_settings()
    genai.configure(api_key=s.gemini_api_key)
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=_SYSTEM_APPEAL,
    )


async def trace_denial(
    query: str,
    document_id: str | None = None,
    generate_appeal: bool = False,
    patient_name: str | None = None,
) -> dict:
    # 1. Strip PHI before any processing
    stripped    = strip_phi(query)
    clean_query = stripped.clean_text

    # 2. Search ChromaDB
    chunks = query_rules(clean_query, document_id=document_id, n=5)

    if not chunks:
        return {
            "status":                "no_rules",
            "clinician_explanation": "No matching policy rules found. Please upload the insurance policy PDF first.",
            "patient_explanation":   "We couldn't find the specific rule that caused this denial. Please make sure your insurance policy has been uploaded.",
            "clinician_actions":     ["Upload the insurance policy PDF", "Re-run this trace after indexing"],
            "patient_actions":       ["Contact your insurance company for a written explanation", "Ask for the specific policy rule in writing"],
            "confidence":            0.0,
            "verified":              False,
            "source_chunks":         [],
        }

    # 3. Build anonymized context
    rule_context = "\n\n---\n\n".join([
        f"[Page {c['page_num']} — {c['document_name']}]\n{c['text']}"
        for c in chunks[:3]
    ])

    # 4. Call Gemini for dual explanation
    prompt = f"""DENIAL REASON / CODE:
{clean_query}

RELEVANT POLICY RULES FOUND:
{rule_context}

Generate the dual explanation JSON. Return ONLY raw JSON, no markdown."""

    try:
        model    = _get_gemini()
        response = model.generate_content(prompt)
        raw      = response.text.strip()
        raw      = re.sub(r"^```json\s*", "", raw)
        raw      = re.sub(r"^```\s*",     "", raw)
        raw      = re.sub(r"\s*```$",     "", raw)
        data     = json.loads(raw)

    except json.JSONDecodeError:
        logger.warning("Gemini returned non-JSON, using fallback")
        data = {
            "clinician_explanation": "Explanation unavailable — please try again.",
            "patient_explanation":   "We found a matching rule but couldn't format the explanation. Please try again.",
            "clinician_actions":     ["Review source rules tab for matched policy text"],
            "patient_actions":       ["Contact your insurance company for clarification"],
            "source_rule":           chunks[0]["document_name"] if chunks else "",
            "appeal_deadline":       None,
            "confidence_reasoning":  "JSON parse error",
        }
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise

    # 5. Confidence score from cosine distance
    top_distance   = chunks[0]["distance"] if chunks else 1.0
    raw_confidence = max(0.0, min(1.0, 1.0 - (top_distance / 1.5)))

    # 6. Hallucination guard
    verified = _verify_against_source(
        explanation   = data.get("clinician_explanation", ""),
        source_chunks = [c["text"] for c in chunks],
    )

    # 7. Appeal letter — uses separate Gemini instance with plain text instruction
    appeal_letter = None
    if generate_appeal:
        appeal_letter = await _generate_appeal_letter(
            denial_reason         = clean_query,
            clinician_explanation = data.get("clinician_explanation", ""),
            patient_name          = patient_name,
        )

    return {
        "status":                "success",
        "clinician_explanation": data.get("clinician_explanation", ""),
        "patient_explanation":   data.get("patient_explanation", ""),
        "clinician_actions":     data.get("clinician_actions", []),
        "patient_actions":       data.get("patient_actions", []),
        "source_rule":           data.get("source_rule", chunks[0]["document_name"] if chunks else ""),
        "page_num":              chunks[0]["page_num"] if chunks else None,
        "appeal_deadline":       data.get("appeal_deadline"),
        "confidence":            round(raw_confidence, 2),
        "confidence_reasoning":  data.get("confidence_reasoning", ""),
        "verified":              verified,
        "source_chunks":         chunks,
        "appeal_letter":         appeal_letter,
        "had_phi_in_query":      stripped.had_phi,
    }


def _verify_against_source(explanation: str, source_chunks: list[str]) -> bool:
    if not source_chunks:
        return False
    source = " ".join(source_chunks).lower()
    claims = re.findall(
        r"section\s+[\d\.]+|"
        r"\$[\d,]+|"
        r"\d+\s*days?|"
        r"\d+\s*months?|"
        r"prior\s+auth\w*|"
        r"medical\s+necessit\w+|"
        r"not\s+covered|"
        r"covered\s+benefit",
        explanation.lower()
    )
    if not claims:
        return True
    hits = sum(1 for c in claims if c in source)
    return (hits / len(claims)) >= 0.70


async def _generate_appeal_letter(
    denial_reason: str,
    clinician_explanation: str,
    patient_name: str | None,
) -> str:
    """
    Generate a formal appeal letter as plain text.
    Uses a separate Gemini instance with _SYSTEM_APPEAL instruction
    to ensure plain text output, never JSON.
    """
    name_line = f"Patient: {patient_name}" if patient_name else ""

    prompt = f"""Write a formal insurance appeal letter with these details:

Denial reason: {denial_reason}
Clinical context: {clinician_explanation[:500]}
{name_line}

The letter must:
- Start with [DATE]
- Be addressed to: Insurance Company Appeals Department
- Reference the denial and request reconsideration
- Cite the relevant policy rule
- Use professional language
- Include these placeholders exactly: [DATE], [CLAIM NUMBER], [PATIENT NAME], [MEMBER ID], [PROVIDER NAME], [Provider Address], [Provider Phone Number]
- Request written response within 30 days
- End with: Sincerely, [PROVIDER NAME]

Write the letter now. Plain text only. Start with [DATE]."""

    try:
        model    = _get_gemini_appeal()
        response = model.generate_content(prompt)
        letter   = response.text.strip()

        # Safety check: if Gemini still returned JSON, extract or reject it
        if letter.startswith('{'):
            try:
                parsed = json.loads(letter)
                # Try to find any letter-like field
                for key in ["appeal_letter", "letter", "text", "content"]:
                    if key in parsed and isinstance(parsed[key], str):
                        return parsed[key]
                # If no letter field found, generate a fallback
                logger.warning("Appeal letter came back as JSON with no letter field, using fallback")
                return _fallback_letter(denial_reason, patient_name)
            except json.JSONDecodeError:
                pass

        return letter

    except Exception as e:
        logger.error(f"Appeal letter generation failed: {e}")
        return _fallback_letter(denial_reason, patient_name)


def _fallback_letter(denial_reason: str, patient_name: str | None) -> str:
    """
    Simple fallback appeal letter if Gemini fails.
    Always returns clean plain text.
    """
    name = patient_name or "[PATIENT NAME]"
    return f"""[DATE]

Insurance Company Appeals Department
[Insurance Company Address]

RE: Formal Appeal for {name}
Claim Number: [CLAIM NUMBER]
Member ID: [MEMBER ID]

To Whom It May Concern,

I am writing to formally appeal the denial of the insurance claim for {name}.

The claim was denied with the following reason: {denial_reason}

We respectfully disagree with this determination and request a complete review of this decision. The service provided was medically necessary and appropriate for the patient's condition.

We request that you reconsider this denial and provide coverage for the service in question. Please provide a written response within 30 days of receiving this letter.

If you require any additional documentation or medical records to support this appeal, please do not hesitate to contact us.

Thank you for your prompt attention to this matter.

Sincerely,

[PROVIDER NAME]
[Provider Address]
[Provider Phone Number]"""