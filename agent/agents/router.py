"""
router.py — Detect which career-ops mode to run from user input.
Mirrors the routing logic in SKILL.md.
"""

import re

# Explicit sub-commands
KNOWN_COMMANDS = {
    "oferta", "ofertas", "contacto", "deep", "pdf", "training",
    "project", "tracker", "pipeline", "apply", "scan", "batch",
    "patterns", "followup", "latex",
}

# Keywords that suggest a JD was pasted or a URL provided
JD_SIGNALS = [
    "responsibilities", "requirements", "qualifications",
    "about the role", "we're looking for", "what you'll do",
    "what we're looking for", "minimum qualifications",
    "preferred qualifications", "job description",
    "http://", "https://", "linkedin.com/jobs", "greenhouse.io",
    "lever.co", "ashbyhq.com", "workday.com",
]


def detect_mode(user_input: str) -> tuple[str, str]:
    """
    Returns (mode, cleaned_input).
    mode: one of KNOWN_COMMANDS or 'auto-pipeline' or 'discovery'
    cleaned_input: input with command prefix stripped if present
    """
    stripped = user_input.strip()
    lower = stripped.lower()

    # Empty input → show menu
    if not stripped:
        return "discovery", ""

    # Check if first word is a known command
    first_word = lower.split()[0]
    if first_word in KNOWN_COMMANDS:
        rest = stripped[len(first_word):].strip()
        return first_word, rest

    # Check for JD signals → auto-pipeline
    for signal in JD_SIGNALS:
        if signal in lower:
            return "auto-pipeline", stripped

    # Default: treat as auto-pipeline with the full input
    return "auto-pipeline", stripped
