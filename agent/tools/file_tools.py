"""
file_tools.py — Read/write tools for career-ops agent.
All paths are relative to the project root (career-ops/).
"""

import json
from datetime import date
from pathlib import Path

from langchain_core.tools import tool

ROOT = Path(__file__).parent.parent.parent  # career-ops/


# ── Readers ─────────────────────────────────────────────────────────

@tool
def read_cv() -> str:
    """Read the candidate's CV from cv.md."""
    p = ROOT / "cv.md"
    return p.read_text() if p.exists() else "cv.md not found."


@tool
def read_profile() -> str:
    """Read candidate profile (profile.yml + _profile.md archetypes)."""
    profile = ROOT / "config" / "profile.yml"
    archetypes = ROOT / "modes" / "_profile.md"
    out = []
    if profile.exists():
        out.append(f"=== config/profile.yml ===\n{profile.read_text()}")
    if archetypes.exists():
        out.append(f"=== modes/_profile.md ===\n{archetypes.read_text()}")
    return "\n\n".join(out) if out else "Profile files not found."


@tool
def read_article_digest() -> str:
    """Read article-digest.md for detailed proof points (optional)."""
    p = ROOT / "article-digest.md"
    return p.read_text() if p.exists() else "article-digest.md not found — use cv.md only."


@tool
def read_applications_tracker() -> str:
    """Read the current applications tracker (data/applications.md)."""
    p = ROOT / "data" / "applications.md"
    return p.read_text() if p.exists() else "Tracker not found."


@tool
def read_scan_history() -> str:
    """Read data/scan-history.tsv to detect reposted jobs."""
    p = ROOT / "data" / "scan-history.tsv"
    if not p.exists():
        return "scan-history.tsv not found — no reposting data available."
    # Return last 200 lines to keep context bounded
    lines = p.read_text().splitlines()
    return "\n".join(lines[-200:])


@tool
def read_cv_template() -> str:
    """Read the HTML CV template for PDF generation."""
    p = ROOT / "templates" / "cv-template.html"
    return p.read_text() if p.exists() else "cv-template.html not found."

@tool
def read_file(filepath: str) -> str:
    """
    Read any arbitrary text file within the workspace.
    filepath: relative path to the file (e.g. 'modes/pdf.md').
    """
    p = ROOT / filepath
    if not p.exists():
        return f"{filepath} not found."
    return p.read_text()


# ── Writers ──────────────────────────────────────────────────────────

@tool
def save_report(filename: str, content: str) -> str:
    """
    Save an evaluation report to reports/.
    filename: e.g. '001-libra-ai-2026-04-21.md'
    content: full markdown report text
    """
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    path = reports_dir / filename
    path.write_text(content)
    return f"Report saved: reports/{filename}"


@tool
def write_tracker_tsv(filename: str, content: str) -> str:
    """
    Write a TSV tracker addition to batch/tracker-additions/.
    filename: e.g. '001-libra-ai.tsv'
    content: single tab-separated line (9 columns)
    """
    additions_dir = ROOT / "batch" / "tracker-additions"
    additions_dir.mkdir(parents=True, exist_ok=True)
    path = additions_dir / filename
    path.write_text(content)
    return f"TSV written: batch/tracker-additions/{filename}"


@tool
def write_cv_html(filename: str, html_content: str) -> str:
    """
    Write a rendered CV HTML file to /tmp/ for PDF conversion.
    filename: e.g. 'cv-tanuj-parmar-libra-ai.html'
    Returns the full path written.
    """
    path = Path("/tmp") / filename
    path.write_text(html_content, encoding="utf-8")
    return str(path)


@tool
def get_next_report_number() -> str:
    """
    Calculate the next sequential report number (3-digit zero-padded).
    Reads reports/ directory and returns e.g. '002'.
    """
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    existing = sorted(reports_dir.glob("*.md"))
    if not existing:
        return "001"
    last = existing[-1].name
    try:
        num = int(last.split("-")[0])
        return str(num + 1).zfill(3)
    except (ValueError, IndexError):
        return "001"


@tool
def get_today() -> str:
    """Return today's date as YYYY-MM-DD."""
    return date.today().isoformat()
