"""
Agent 2: Decision Tracer + Dual Explainer + Hallucination Guard

Production additions:
- Observability: Langfuse traces every call (token count, latency, errors)
- Failure handling: tenacity retry with exponential backoff
- Graceful degradation: fallback response if Gemini is down
"""

import json
import logging
import re
import google.generativeai as genai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from config import get_settings
from security.phi_stripper import strip_phi
from agents.policy_parser import query_rules
from observability import trace_agent_call, log_gemini_call, log_retrieval, get_langfuse

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

_SYSTEM_APPEAL = """You are a healthcare appeal letter writer.
You write formal, professional insurance appeal letters.
CRITICAL: Return ONLY the letter text as plain text.
Do NOT return JSON. Do NOT use markdown. Do NOT add any explanation before or after.
Start the letter directly with [DATE]. End with the signature."""


def _get_gemini():
    s = get_settings()
    genai.configure(api_key=s.gemini_api_key)
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=_SYSTEM_TRACER,
    )


def _get_gemini_appeal():
    s = get_settings()
    genai.configure(api_key=s.gemini_api_key)
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=_SYSTEM_APPEAL,
    )


# ── Failure Handling — Retry with exponential backoff ─────────────────────────
# If Gemini returns a 429 (rate limit) or 503 (service unavailable),
# retry up to 3 times with increasing delays: 2s → 4s → 8s
# This handles transient failures gracefully without crashing the request.

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _call_gemini_with_retry(model, prompt: str) -> str:
    """
    Call Gemini with automatic retry on failure.
    Retries up to 3 times with exponential backoff (2s, 4s, 8s).
    """
    response = model.generate_content(prompt)
    return response.text.strip()


def _fallback_explanation(denial_reason: str) -> dict:
    """
    Fallback response when Gemini is completely unavailable.
    Returns a structured response that degrades gracefully.
    """
    return {
        "clinician_explanation": (
            f"The claim was denied with reason: {denial_reason}. "
            "AI explanation is temporarily unavailable. "
            "Please check the Source Rules tab for matched policy text "
            "and refer to the policy document directly."
        ),
        "patient_explanation": (
            "Your claim was denied. We found matching policy rules but "
            "our AI explanation service is temporarily unavailable. "
            "Please contact your provider's office for assistance."
        ),
        "clinician_actions": [
            "Review the matched policy rules in the Source Rules tab",
            "Contact the insurance company's provider line for clarification",
            "Try again in a few minutes",
        ],
        "patient_actions": [
            "Contact your doctor's office for help understanding this denial",
            "Call the insurance company's member services line",
            "Try again in a few minutes",
        ],
        "source_rule":          "See Source Rules tab",
        "appeal_deadline":      None,
        "confidence_reasoning": "AI service temporarily unavailable — showing matched rules only",
    }


# ── Main Agent Function ────────────────────────────────────────────────────────

@trace_agent_call("denial_tracer")
async def trace_denial(
    query: str,
    document_id: str | None = None,
    generate_appeal: bool = False,
    patient_name: str | None = None,
    recipient_type: str = "insurance",
) -> dict:
    """
    Main denial tracing agent.

    Production features:
    - Langfuse observability (traces every call)
    - Retry with exponential backoff (handles Gemini outages)
    - Graceful degradation (fallback when AI is down)
    - PHI stripping (before any external API call)
    """
    lf = get_langfuse()
    trace = lf.trace(name="trace_denial", input={"query": query[:200]}) if lf else None

    # 1. Strip PHI before any processing
    stripped    = strip_phi(query)
    clean_query = stripped.clean_text

    # 2. Search ChromaDB
    chunks = query_rules(clean_query, document_id=document_id, n=5)

    # Log retrieval to Langfuse
    if trace:
        log_retrieval(trace, clean_query, chunks)

    if not chunks:
        return {
            "status":                "no_rules",
            "clinician_explanation": "No matching policy rules found. Please upload the insurance policy PDF first.",
            "patient_explanation":   "We couldn't find the specific rule that caused this denial. Please make sure your insurance policy has been uploaded.",
            "clinician_actions":     ["Upload the insurance policy PDF", "Re-run this trace after indexing"],
            "patient_actions":       ["Contact your insurance company for a written explanation"],
            "confidence":            0.0,
            "verified":              False,
            "source_chunks":         [],
        }

    # 3. Build context
    rule_context = "\n\n---\n\n".join([
        f"[Page {c['page_num']} — {c['document_name']}]\n{c['text']}"
        for c in chunks[:3]
    ])

    prompt = f"""DENIAL REASON / CODE:
{clean_query}

RELEVANT POLICY RULES FOUND:
{rule_context}

Generate the dual explanation JSON. Return ONLY raw JSON, no markdown."""

    # 4. Call Gemini with retry + fallback
    try:
        model    = _get_gemini()
        raw_text = _call_gemini_with_retry(model, prompt)

        # Log to Langfuse
        if trace:
            log_gemini_call(trace, prompt, raw_text)

        raw  = re.sub(r"^```json\s*", "", raw_text)
        raw  = re.sub(r"^```\s*",     "", raw)
        raw  = re.sub(r"\s*```$",     "", raw)
        data = json.loads(raw)

    except json.JSONDecodeError:
        logger.warning("Gemini returned non-JSON — using fallback explanation")
        data = _fallback_explanation(clean_query)

    except Exception as e:
        # Gemini failed after all retries — degrade gracefully
        logger.error(f"Gemini API error after retries: {e}")
        data = _fallback_explanation(clean_query)

    # 5. Confidence score
    top_distance   = chunks[0]["distance"] if chunks else 1.0
    raw_confidence = max(0.0, min(1.0, 1.0 - (top_distance / 1.5)))

    # 6. Hallucination guard
    verified = _verify_against_source(
        explanation   = data.get("clinician_explanation", ""),
        source_chunks = [c["text"] for c in chunks],
    )

    # 7. Appeal letter
    appeal_letter = None
    if generate_appeal:
        appeal_letter = await _generate_appeal_letter(
            denial_reason         = clean_query,
            clinician_explanation = data.get("clinician_explanation", ""),
            patient_name          = patient_name,
            recipient_type        = recipient_type,
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
    recipient_type: str = "insurance",
) -> str:
    """
    Generate appeal letter with different prompts per recipient type.

    recipient_type:
    - "insurance"    → formal clinical appeal to insurance company
    - "patient"      → plain English summary from doctor to patient
    - "patient_self" → personal appeal written for the patient to send
    """
    if recipient_type == "patient":
        prompt = f"""Write a brief, empathetic email from a doctor to their patient.

Denial reason: {denial_reason}
Patient name: {patient_name or 'the patient'}

The email should:
- Be warm and reassuring
- Explain in plain English what happened with their insurance claim
- Tell them what the doctor's office is doing about it
- Tell them what they need to do if anything
- Be short — 3 to 4 paragraphs maximum
- Start with: Dear {patient_name or 'Patient'},

Write only the email body. Plain text only."""

    elif recipient_type == "patient_self":
        prompt = f"""Write a personal insurance appeal letter FROM a patient TO their insurance company.

Denial reason: {denial_reason}
Patient name: {patient_name or '[PATIENT NAME]'}

The letter must:
- Be written in first person (I, my, me)
- Include a personal statement about why this service was needed
- Reference the denial and request reconsideration
- State the right to appeal
- Request written response within 30 days
- Include placeholders: [DATE], [MEMBER ID], [CLAIM NUMBER], [DATE OF SERVICE]
- Start with [DATE]

Write only the letter. Plain text. Start with [DATE]."""

    else:
        # Default: formal provider appeal to insurance company
        prompt = f"""Write a formal insurance appeal letter from a healthcare provider to an insurance company.

Denial reason: {denial_reason}
Clinical context: {clinician_explanation[:500]}
Patient name: {patient_name or '[PATIENT NAME]'}

The letter must:
- Be formal and clinical in tone
- Cite the specific policy rule
- Argue medical necessity
- Include placeholders: [DATE], [CLAIM NUMBER], [PATIENT NAME], [MEMBER ID], [PROVIDER NAME], [Provider Address], [Provider Phone Number]
- Request written response within 30 days
- Start with [DATE]

Write only the letter. Plain text. Start with [DATE]."""

    try:
        model    = _get_gemini_appeal()
        letter   = _call_gemini_with_retry(model, prompt)

        # Safety check — if Gemini still returned JSON somehow
        if letter.strip().startswith('{'):
            try:
                parsed = json.loads(letter)
                for key in ["appeal_letter", "letter", "text", "content"]:
                    if key in parsed and isinstance(parsed[key], str):
                        return parsed[key]
            except json.JSONDecodeError:
                pass
            return _fallback_letter(denial_reason, patient_name, recipient_type)

        return letter

    except Exception as e:
        logger.error(f"Appeal letter generation failed after retries: {e}")
        return _fallback_letter(denial_reason, patient_name, recipient_type)


def _fallback_letter(denial_reason: str, patient_name: str | None, recipient_type: str) -> str:
    """Clean fallback letter when AI is unavailable."""
    name = patient_name or "[PATIENT NAME]"

    if recipient_type == "patient":
        return f"""Dear {name},

I am writing to inform you about the status of your recent insurance claim.

Your claim was denied with the following reason: {denial_reason}

Our office is currently reviewing this denial and will take appropriate steps to address it on your behalf. We will keep you informed of any updates.

If you have any questions, please do not hesitate to contact our office.

Sincerely,
[PROVIDER NAME]"""

    return f"""[DATE]

Insurance Company Appeals Department
[Insurance Company Address]

RE: Formal Appeal — {name}
Claim Number: [CLAIM NUMBER]
Member ID: [MEMBER ID]

To Whom It May Concern,

This letter serves as a formal appeal regarding the denial of the insurance claim for {name}.

Denial reason: {denial_reason}

We respectfully request a complete review of this decision. The service provided was medically necessary and appropriate. We are prepared to provide all supporting clinical documentation.

Please respond in writing within 30 days.

Sincerely,
[PROVIDER NAME]
[Provider Address]
[Provider Phone Number]"""