"""
loader.py — Load modes/*.md prompt files as system prompt strings.
These are the same files used by the Claude Code skill — unchanged.
"""

from pathlib import Path

ROOT = Path(__file__).parent.parent.parent  # career-ops/
MODES_DIR = ROOT / "modes"


def load_mode(mode: str) -> str:
    """
    Load _shared.md + modes/{mode}.md and return combined system prompt.
    Falls back gracefully if a file is missing.
    """
    parts = []

    shared = MODES_DIR / "_shared.md"
    if shared.exists():
        parts.append(shared.read_text())

    mode_file = MODES_DIR / f"{mode}.md"
    if mode_file.exists():
        parts.append(mode_file.read_text())
    else:
        parts.append(f"# Mode: {mode}\nEvaluate the input and produce a structured report.")

    return "\n\n---\n\n".join(parts)


def load_standalone(mode: str) -> str:
    """Load only modes/{mode}.md (no _shared.md). For tracker, deep, patterns."""
    mode_file = MODES_DIR / f"{mode}.md"
    if mode_file.exists():
        return mode_file.read_text()
    return f"# Mode: {mode}\nProcess the request."


# Pre-built system prompts per mode
SYSTEM_PROMPTS = {
    "oferta":        lambda: load_mode("oferta"),
    "auto-pipeline": lambda: load_mode("auto-pipeline"),
    "pdf":           lambda: load_mode("pdf"),
    "scan":          lambda: load_mode("scan"),
    "tracker":       lambda: load_standalone("tracker"),
    "patterns":      lambda: load_standalone("patterns"),
    "followup":      lambda: load_standalone("followup"),
    "deep":          lambda: load_standalone("deep"),
    "training":      lambda: load_standalone("training"),
    "project":       lambda: load_standalone("project"),
    "contacto":      lambda: load_mode("contacto"),
    "pipeline":      lambda: load_mode("pipeline"),
    "ofertas":       lambda: load_mode("ofertas"),
}


def get_system_prompt(mode: str) -> str:
    loader = SYSTEM_PROMPTS.get(mode)
    if loader:
        return loader()
    # Unknown mode — load generically
    return load_mode(mode)
