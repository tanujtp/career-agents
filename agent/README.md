# career-ops — LangChain + OpenAI Agent

Same job search pipeline, zero Claude Code dependency.
Uses the same `modes/*.md` prompt files — only the runtime changes.

## Architecture

```
agent/
├── main.py              CLI entrypoint
├── agents/
│   ├── router.py        Detects mode from user input
│   └── evaluator.py     LangChain agents per mode
├── tools/
│   ├── file_tools.py    Read cv.md, write reports, tracker TSV
│   ├── web_tools.py     Fetch JDs, DuckDuckGo search (free)
│   └── bash_tools.py    Run generate-pdf.mjs, merge-tracker.mjs, scan.mjs
└── prompts/
    └── loader.py        Loads modes/*.md as system prompts
```

**Flow:**
```
User input
  → router.py detects mode
  → loader.py loads modes/_shared.md + modes/{mode}.md as system prompt
  → evaluator.py builds LangChain OpenAI tools agent
  → agent calls tools (read CV, fetch JD, search web, save report...)
  → merge-tracker.mjs merges TSV into applications.md
```

## Setup

```bash
cd career-ops/agent

# Install dependencies
pip install -r requirements.txt

# Install Playwright for PDF generation (one-time)
playwright install chromium

# Configure
cp .env.example ../.env
# Edit .env — add your OPENAI_API_KEY
```

## Usage

```bash
# From career-ops root:

# Show menu
python agent/main.py

# Evaluate a job (full A-G report + save to reports/)
python agent/main.py https://jobs.lever.co/company/job-id

# Evaluate only (no PDF)
python agent/main.py oferta https://jobs.lever.co/company/job-id

# Generate PDF CV for a job
python agent/main.py pdf https://jobs.lever.co/company/job-id

# Show tracker
python agent/main.py tracker

# Scan portals for new jobs (zero tokens — calls Node.js directly)
python agent/main.py scan

# Deep company research
python agent/main.py deep "Stripe"

# Analyze rejection patterns
python agent/main.py patterns

# Follow-up cadence
python agent/main.py followup
```

## Model options

Set `CAREER_OPS_MODEL` in `.env`:

| Model | Cost per eval | Quality |
|---|---|---|
| `gpt-4o` (default) | ~$0.05–0.15 | Best |
| `gpt-4o-mini` | ~$0.005–0.015 | Good |
| `gpt-4-turbo` | ~$0.10–0.20 | Best (slower) |

## Swap to a free model

Change one line in `agents/evaluator.py`:

```python
# Free — Gemini 2.5 Pro (1500 requests/day free)
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", google_api_key="...")

# Free — Groq (llama3.1-70b, fast)
from langchain_groq import ChatGroq
llm = ChatGroq(model="llama-3.1-70b-versatile", groq_api_key="...")

# Free — Local Ollama (no internet needed, needs GPU/RAM)
from langchain_ollama import ChatOllama
llm = ChatOllama(model="qwen2.5:32b")
```

The prompts (`modes/*.md`), data files, and Node.js scripts are unchanged.

## What doesn't change

- `cv.md`, `config/profile.yml`, `modes/_profile.md` — your personal data
- `modes/*.md` — all prompt logic (unchanged)
- `scan.mjs`, `generate-pdf.mjs`, `merge-tracker.mjs` — Node.js scripts (called via subprocess)
- `reports/`, `data/`, `output/` — all output files
