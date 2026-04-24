"""
evaluator.py — Core LangChain agent that runs career-ops evaluations.
Uses OpenAI GPT-4o by default. Swap model in config or via env var.
"""

import os
from typing import Optional

from langchain_classic.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from agent.prompts import get_system_prompt
from agent.tools import ALL_TOOLS

# ── Model config ─────────────────────────────────────────────────────

def build_llm(model: Optional[str] = None, temperature: float = 0) -> "ChatOpenAI":
    """
    Build the LLM. Override model via CAREER_OPS_MODEL env var.
    Defaults to gpt-4o — best reasoning for multi-block evaluations.
    Cheaper option: gpt-4o-mini (~10x cheaper, slightly lower quality).
    """
    selected_model = model or os.getenv("CAREER_OPS_MODEL", "gpt-4o")
    return ChatOpenAI(
        model=selected_model,
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY"),
        streaming=True,
    )


# ── Agent builder ────────────────────────────────────────────────────

def build_agent(mode: str, model: Optional[str] = None) -> AgentExecutor:
    """
    Build a LangChain OpenAI tools agent for the given career-ops mode.
    The system prompt is loaded from modes/_shared.md + modes/{mode}.md —
    the same files used by the Claude Code skill.
    """
    system_prompt = get_system_prompt(mode)

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    llm = build_llm(model)
    agent = create_openai_tools_agent(llm, ALL_TOOLS, prompt)

    return AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS,
        verbose=True,
        max_iterations=25,
        handle_parsing_errors=True,
        return_intermediate_steps=False,
    )


# ── Mode runners ─────────────────────────────────────────────────────

def run_evaluation(job_input: str, model: Optional[str] = None) -> str:
    """
    Run a full A-G evaluation (oferta mode).
    job_input: URL or pasted JD text.
    """
    executor = build_agent("oferta", model)
    result = executor.invoke({
        "input": (
            f"Evaluate this job posting and produce the full A-G evaluation report.\n\n"
            f"Job input: {job_input}"
        )
    })
    return result.get("output", "")


def run_auto_pipeline(job_input: str, model: Optional[str] = None) -> str:
    """
    Run the full auto-pipeline: evaluate + save report + generate PDF + update tracker.
    job_input: URL or pasted JD text.
    """
    executor = build_agent("auto-pipeline", model)
    result = executor.invoke({
        "input": (
            f"Run the full auto-pipeline for this job: evaluate (A-G), save the report, "
            f"generate a PDF CV, and update the tracker.\n\n"
            f"Job input: {job_input}"
        )
    })
    return result.get("output", "")


def run_tracker(action: str = "") -> str:
    """Show tracker stats or update a status."""
    executor = build_agent("tracker")
    input_text = action if action else "Show the full applications tracker with statistics."
    result = executor.invoke({"input": input_text})
    return result.get("output", "")


def run_pdf(job_input: str, model: Optional[str] = None) -> str:
    """Generate an ATS-optimized PDF CV for a specific job."""
    executor = build_agent("pdf", model)
    result = executor.invoke({
        "input": (
            f"Generate an ATS-optimized PDF CV for this job. "
            f"Read the CV, extract keywords, personalize the summary, "
            f"and produce the PDF.\n\nJob: {job_input}"
        )
    })
    return result.get("output", "")


def run_scan(company: str = "") -> str:
    """Trigger the zero-token portal scan via scan.mjs."""
    executor = build_agent("scan")
    input_text = (
        f"Run the portal scan for company: {company}"
        if company else
        "Run the portal scan for all configured companies in portals.yml."
    )
    result = executor.invoke({"input": input_text})
    return result.get("output", "")


def run_patterns() -> str:
    """Analyze rejection patterns from the tracker."""
    executor = build_agent("patterns")
    result = executor.invoke({
        "input": "Read the applications tracker and analyze rejection patterns. "
                 "What roles/companies/archetypes are performing best? What should change?"
    })
    return result.get("output", "")


def run_followup() -> str:
    """Check follow-up cadence and flag overdue applications."""
    executor = build_agent("followup")
    result = executor.invoke({
        "input": "Read the applications tracker, check follow-up cadence, "
                 "flag overdue applications, and generate draft follow-up messages."
    })
    return result.get("output", "")


def run_deep_research(company: str) -> str:
    """Run deep company research."""
    executor = build_agent("deep")
    result = executor.invoke({
        "input": f"Run deep research on this company: {company}. "
                 "Cover: business model, culture, recent news, hiring signals, "
                 "team structure, and fit assessment."
    })
    return result.get("output", "")


def run_generic(mode: str, user_input: str, model: Optional[str] = None) -> str:
    """Run any mode with raw user input."""
    executor = build_agent(mode, model)
    result = executor.invoke({"input": user_input})
    return result.get("output", "")
