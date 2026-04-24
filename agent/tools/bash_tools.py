"""
bash_tools.py — Run existing Node.js scripts via subprocess.
These scripts have zero LLM dependency — pure Node.js utilities.
"""

import subprocess
from pathlib import Path

from langchain_core.tools import tool

ROOT = Path(__file__).parent.parent.parent  # career-ops/


def _run(cmd: list[str], cwd: Path = ROOT) -> str:
    """Run a command and return combined stdout+stderr."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=120,
    )
    out = result.stdout.strip()
    err = result.stderr.strip()
    if result.returncode != 0 and err:
        return f"ERROR (exit {result.returncode}):\n{err}\n{out}"
    return out or err or "Done."


@tool
def generate_pdf(html_path: str, output_path: str, paper_format: str = "a4") -> str:
    """
    Convert an HTML file to PDF using Playwright via generate-pdf.mjs.
    html_path: absolute path to the HTML file (e.g. /tmp/cv-tanuj-libra-ai.html)
    output_path: relative path for output (e.g. output/cv-tanuj-libra-ai-2026-04-21.pdf)
    paper_format: 'a4' (default) or 'letter' (US/Canada)
    Returns path to generated PDF or error message.
    """
    return _run([
        "node", "generate-pdf.mjs",
        html_path,
        output_path,
        f"--format={paper_format}",
    ])


@tool
def merge_tracker() -> str:
    """
    Merge pending TSV additions from batch/tracker-additions/ into
    data/applications.md. Run after writing tracker TSV files.
    """
    return _run(["node", "merge-tracker.mjs"])


@tool
def run_portal_scan(company: str = "") -> str:
    """
    Run the zero-token portal scanner (scan.mjs).
    Hits Greenhouse/Ashby/Lever APIs directly, deduplicates, and appends
    new offers to data/pipeline.md and data/scan-history.tsv.
    company: optional — scan a single company (e.g. 'Cohere'). Empty = scan all.
    """
    cmd = ["node", "scan.mjs"]
    if company:
        cmd += ["--company", company]
    return _run(cmd)


@tool
def verify_pipeline() -> str:
    """Run pipeline health check (verify-pipeline.mjs). Returns any issues found."""
    return _run(["node", "verify-pipeline.mjs"])
