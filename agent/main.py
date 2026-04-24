#!/usr/bin/env python3
"""
main.py — career-ops CLI (LangChain + OpenAI edition)

Usage:
  python agent/main.py                            # show menu
  python agent/main.py <URL or JD text>           # auto-pipeline
  python agent/main.py oferta <URL or JD text>    # evaluate only
  python agent/main.py tracker                    # show tracker
  python agent/main.py pdf <URL or JD text>       # generate PDF only
  python agent/main.py onboard <resume_path>      # setup profile from resume
  python agent/main.py scan                       # scan portals
  python agent/main.py deep <company name>        # deep research
  python agent/main.py patterns                   # rejection patterns
  python agent/main.py followup                   # follow-up cadence

Environment variables:
  OPENAI_API_KEY      (required)
  CAREER_OPS_MODEL    (optional, default: gpt-4o)
                      Options: gpt-4o | gpt-4o-mini | gpt-4-turbo
"""

import os
import sys
from pathlib import Path

# Ensure project root is in path so `from agent.X import Y` works
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from agent.agents import (
    detect_mode,
    run_evaluation,
    run_auto_pipeline,
    run_tracker,
    run_pdf,
    run_scan,
    run_patterns,
    run_followup,
    run_deep_research,
    run_generic,
)

MENU = """
career-ops — AI Job Search Pipeline (LangChain + OpenAI)
─────────────────────────────────────────────────────────
Commands:
  python agent/main.py <URL or JD>     → AUTO-PIPELINE (evaluate + report + PDF + tracker)
  python agent/main.py oferta <input>  → Evaluation only (A-G blocks)
  python agent/main.py pdf <input>     → Generate ATS-optimized PDF CV
  python agent/main.py tracker         → Show application tracker + stats
  python agent/main.py onboard <path>  → Parse resume and generate profile
  python agent/main.py scan            → Scan job portals for new offers
  python agent/main.py deep <company>  → Deep company research
  python agent/main.py patterns        → Analyze rejection patterns
  python agent/main.py followup        → Follow-up cadence check
  python agent/main.py ofertas         → Compare multiple offers

Model: {model}  (override with CAREER_OPS_MODEL env var)
"""


def check_env() -> bool:
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY is not set.")
        print("  Set it in .env or export OPENAI_API_KEY=sk-...")
        return False
    return True


def main():
    if not check_env():
        sys.exit(1)

    model = os.getenv("CAREER_OPS_MODEL", "gpt-4o")
    args = sys.argv[1:]

    # No args → show menu
    if not args:
        print(MENU.format(model=model))
        return

    user_input = " ".join(args)
    if args[0].lower() == "onboard":
        if len(args) < 2:
            print("Please provide a path to your resume: python agent/main.py onboard <path>")
            sys.exit(1)
        from agent.onboard import onboard_user
        onboard_user(args[1], model)
        return

    mode, payload = detect_mode(user_input)

    print(f"\n[career-ops] Mode: {mode} | Model: {model}\n")
    print("─" * 60)

    try:
        if mode == "discovery":
            print(MENU.format(model=model))

        elif mode in ("auto-pipeline", "oferta") and not payload:
            print("Please provide a job URL or paste a job description.")
            print("Example: python agent/main.py https://jobs.lever.co/company/job-id")

        elif mode == "auto-pipeline":
            result = run_auto_pipeline(payload, model)
            print(result)

        elif mode == "oferta":
            result = run_evaluation(payload, model)
            print(result)

        elif mode == "tracker":
            result = run_tracker(payload)
            print(result)

        elif mode == "pdf":
            if not payload:
                print("Please provide a job URL or JD text for PDF generation.")
            else:
                result = run_pdf(payload, model)
                print(result)

        elif mode == "scan":
            result = run_scan(payload)
            print(result)

        elif mode == "patterns":
            result = run_patterns()
            print(result)

        elif mode == "followup":
            result = run_followup()
            print(result)

        elif mode == "deep":
            if not payload:
                print("Please provide a company name. Example: python agent/main.py deep Stripe")
            else:
                result = run_deep_research(payload)
                print(result)

        else:
            # Any other mode (ofertas, contacto, training, project, etc.)
            result = run_generic(mode, payload or user_input, model)
            print(result)

    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        raise


if __name__ == "__main__":
    main()
