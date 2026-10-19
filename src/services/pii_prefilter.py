import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

@dataclass
class RedactionResult:
    sanitized_text: str
    detected_types: List[str]
    has_pii: bool
    token_map: Dict[str, str] = field(default_factory=dict, repr=False)

class PIIPreFilter:
    """Fast regex pre-screener for EU & German PII ensuring zero raw PII emission."""

    PATTERNS: List[Tuple[str, re.Pattern]] = [
        # Credit / Debit Cards (16 digits separated by dashes or spaces)
        ("CREDIT_CARD", re.compile(r"\b(?:\d{4}[ -]){3}\d{4}\b|\b\d{16}\b")),
        # SEPA / EU / German IBAN (2 letter country code + up to 32 alphanumeric chars, optional spacing)
        ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[0-9A-Z]{4}){3,7}(?:\s?[0-9A-Z]{1,4})?\b|\b[A-Z]{2}\d{2}[0-9A-Z]{12,30}\b", re.IGNORECASE)),
        # German Steuer-ID (11 digits, continuous or spaced like 12 345 678 901 / 123 456 789 01)
        ("STEUER_ID", re.compile(r"\b\d{2}\s\d{3}\s\d{3}\s\d{3}\b|\b\d{3}\s\d{3}\s\d{3}\s\d{2}\b|\b\d{11}\b")),
        # German Passport format (Letter + 8 alphanumeric digits with at least 1 number to avoid English words)
        ("PASSPORT", re.compile(r"\b[A-Z](?=[A-Z0-9]*\d)[A-Z0-9]{8}\b")),
        # Email address
        ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
        # Salary / currency figures (e.g., 95000 €, 120.000 €, 15.000 EUR, 15000 eur, €120,000)
        ("SALARY", re.compile(r"(?:€|EUR)\s*\d{1,7}(?:[.,]\d{3})*(?:,\d{2})?|\b\d{1,7}(?:[.,]\d{3})*(?:,\d{2})?\s*(?:€|EUR|\bEUR\b)", re.IGNORECASE)),
    ]

    def sanitize(self, text: str) -> RedactionResult:
        sanitized = text
        detected: List[str] = []
        token_map: Dict[str, str] = {}
        type_counters: Dict[str, int] = {}

        for pii_type, pattern in self.PATTERNS:
            matches = list(pattern.finditer(sanitized))
            if matches:
                if pii_type not in detected:
                    detected.append(pii_type)
                # Replace matches from end to beginning to preserve string offsets
                for match in reversed(matches):
                    original_val = match.group(0)
                    # Check if already a redacted token
                    if original_val.startswith("[REDACTED_"):
                        continue
                    counter = type_counters.get(pii_type, 0) + 1
                    type_counters[pii_type] = counter
                    token = f"[REDACTED_{pii_type}_{counter}]"
                    token_map[token] = original_val
                    start, end = match.span()
                    sanitized = sanitized[:start] + token + sanitized[end:]

        return RedactionResult(
            sanitized_text=sanitized,
            detected_types=detected,
            has_pii=len(detected) > 0,
            token_map=token_map,
        )

    def detokenize(self, text: str, token_map: Dict[str, str]) -> str:
        """Replaces redacted tokens with original values using the in-memory token map."""
        restored = text
        for token, original in token_map.items():
            restored = restored.replace(token, original)
        return restored
