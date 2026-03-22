"""
Evaluation Suite — measures precision of the Decision Tracer.
Uses Gemini to grade explanation quality (Claude-grades-Claude pattern).
"""

import json
import logging
import re
import google.generativeai as genai
from config import get_settings
from agents.decision_tracer import trace_denial

logger = logging.getLogger(__name__)

TEST_CASES = [
    {"id": "TC001", "denial": "CO-4 - The service is inconsistent with the payer's payment policy.", "expected_keywords": ["prior authorization", "medical necessity", "not covered"]},
    {"id": "TC002", "denial": "CO-11 - The diagnosis is inconsistent with the procedure.", "expected_keywords": ["diagnosis", "procedure", "covered"]},
    {"id": "TC003", "denial": "PR-96 - Non-covered charge.", "expected_keywords": ["benefit", "covered", "exclusion"]},
    {"id": "TC004", "denial": "CO-97 - The benefit for this service is included in the payment for another service.", "expected_keywords": ["bundled", "included", "payment"]},
    {"id": "TC005", "denial": "OA-23 - The impact of prior payer adjudication.", "expected_keywords": ["coordination", "benefits", "primary"]},
]

_EVAL_SYSTEM = """You are an expert healthcare AI evaluator. Score the explanation on three dimensions.
Respond ONLY with valid JSON:
{"accuracy": <1-5>, "clarity": <1-5>, "completeness": <1-5>, "issues": "<or null>", "overall": <1-5>}
5=Excellent, 4=Good, 3=Acceptable, 2=Poor, 1=Wrong/harmful"""


async def run_eval_suite(document_id: str | None = None) -> dict:
    s = get_settings()
    genai.configure(api_key=s.gemini_api_key)
    model   = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=_EVAL_SYSTEM)
    results = []

    for tc in TEST_CASES:
        try:
            trace = await trace_denial(tc["denial"], document_id=document_id)
            source_text    = " ".join(c["text"] for c in trace.get("source_chunks", [])).lower()
            keyword_hits   = sum(1 for kw in tc["expected_keywords"] if kw in source_text)
            retrieval_score= keyword_hits / len(tc["expected_keywords"])

            eval_prompt = f"""Denial: {tc['denial']}
Clinician explanation: {trace.get('clinician_explanation','')[:600]}
Patient explanation: {trace.get('patient_explanation','')[:400]}
Score this."""

            resp   = model.generate_content(eval_prompt)
            raw    = re.sub(r"^```json\s*|```$", "", resp.text.strip())
            scores = json.loads(raw)

            results.append({
                "test_case":       tc["id"],
                "denial":          tc["denial"],
                "retrieval_score": round(retrieval_score, 2),
                "confidence":      trace.get("confidence", 0),
                "verified":        trace.get("verified", False),
                "accuracy":        scores.get("accuracy", 0),
                "clarity":         scores.get("clarity", 0),
                "completeness":    scores.get("completeness", 0),
                "overall":         scores.get("overall", 0),
                "issues":          scores.get("issues"),
                "status":          "pass" if retrieval_score >= 0.5 and scores.get("overall", 0) >= 3 else "fail",
            })
        except Exception as e:
            results.append({"test_case": tc["id"], "status": "error", "error": str(e)})

    passed   = sum(1 for r in results if r.get("status") == "pass")
    avg_conf = sum(r.get("confidence", 0) for r in results) / len(results)
    avg_qual = sum(r.get("overall", 0) for r in results if r.get("overall")) / max(1, len(results))
    avg_retr = sum(r.get("retrieval_score", 0) for r in results) / len(results)

    return {
        "total_cases":         len(results),
        "passed":              passed,
        "pass_rate":           round(passed / len(results), 2),
        "avg_confidence":      round(avg_conf, 2),
        "avg_quality_score":   round(avg_qual, 2),
        "avg_retrieval_score": round(avg_retr, 2),
        "ready_for_production":passed / len(results) >= 0.80 and avg_qual >= 3.5,
        "results":             results,
    }
