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
        # German IBAN (DE + 20 digits, optionally space-separated)
        ("IBAN", re.compile(r"\bDE\d{2}(?:\s?\d{4}){4}\s?\d{2}\b|\bDE\d{20}\b")),
        # German Steuer-ID (11 consecutive digits)
        ("STEUER_ID", re.compile(r"\b\d{11}\b")),
        # German Passport format (Letter + 8 alphanumeric digits)
        ("PASSPORT", re.compile(r"\b[A-Z][0-9A-Z]{8}\b")),
        # Email address
        ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
        # Salary / currency figures (e.g., 120.000 €, 15.000 EUR, €120,000)
        ("SALARY", re.compile(r"(?:€|EUR)\s*\d{1,3}(?:[.,]\d{3})*(?:,\d{2})?|\b\d{1,3}(?:[.,]\d{3})*(?:,\d{2})?\s*(?:€|EUR|\bEUR\b)")),
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
