"""
Strips Protected Health Information (PHI) from text
before it is ever sent to an external LLM API.
Removes: SSNs, phones, emails, DOBs, addresses, MRNs, names.
"""

import re
from dataclasses import dataclass

_PATTERNS = {
    "ssn":     r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
    "phone":   r"\b(\+1[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b",
    "email":   r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
    "dob":     r"\b(0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])[-/](\d{2}|\d{4})\b",
    "mrn":     r"\b(MRN|mrn|Member\s?ID|Policy\s?No\.?)[:\s#]*[A-Z0-9\-]{5,20}\b",
    "address": r"\d{1,5}\s+\w+\s+(St|Ave|Rd|Blvd|Dr|Ln|Way|Ct|Pl)\.?\b",
}

_FIRST_NAMES = {
    "james","john","robert","michael","william","david","richard","joseph",
    "thomas","charles","mary","patricia","jennifer","linda","barbara","elizabeth",
    "susan","jessica","sarah","karen","lisa","nancy","betty","margaret","sandra",
    "ashley","dorothy","kimberly","emily","donna","michelle","carol","amanda",
}


@dataclass
class StrippedResult:
    clean_text:     str
    redacted_items: dict
    had_phi:        bool


def strip_phi(text: str) -> StrippedResult:
    redacted: dict = {}
    clean = text

    for label, pattern in _PATTERNS.items():
        matches = re.findall(pattern, clean, flags=re.IGNORECASE)
        if matches:
            flat = [m if isinstance(m, str) else "".join(m) for m in matches]
            redacted[label] = flat
            clean = re.sub(pattern, f"[{label.upper()}_REDACTED]", clean, flags=re.IGNORECASE)

    name_matches = re.findall(r"\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b", clean)
    names_removed = []
    for first, last in name_matches:
        if first.lower() in _FIRST_NAMES:
            full = f"{first} {last}"
            clean = clean.replace(full, "[NAME_REDACTED]")
            names_removed.append(full)
    if names_removed:
        redacted["name"] = names_removed

    return StrippedResult(clean_text=clean, redacted_items=redacted, had_phi=bool(redacted))


def strip_phi_from_chunks(chunks: list[str]) -> list[str]:
    return [strip_phi(c).clean_text for c in chunks]
