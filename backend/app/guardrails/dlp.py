"""Data-loss-prevention scanning for free-text investigation content.

ATLAS-047 (Guardrails) requires DLP controls on content moving through the
platform. Project Atlas has no AI agent executing prompts yet (ATLAS-040 is
not implemented, so there is nothing to test prompt-injection or model
isolation against) — this module covers only the applicable slice: pattern
matching against text a human types into investigation events,
hypotheses, and recommendations, before it is stored or ever could reach a
future model's context window.
"""
import re

_PATTERNS: dict[str, re.Pattern[str]] = {
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "generic_api_key_assignment": re.compile(
        r"\b(api[_-]?key|secret|password|token)\b\s*[:=]\s*\S{8,}", re.IGNORECASE
    ),
    "private_key_block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}


def find_violations(text: str) -> list[str]:
    """Return the names of every DLP pattern that matched `text`."""
    return [name for name, pattern in _PATTERNS.items() if pattern.search(text)]
