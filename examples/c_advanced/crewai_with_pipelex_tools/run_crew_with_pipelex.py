"""CrewAI crew with Pipelex research pipeline + vanilla dispatch.

Agent 1 (Researcher) calls Pipelex `deep_research` → typed ResearchBrief (Pydantic).
Agent 2 (Publisher) calls Pipelex `compose_report` (PipeCompose, deterministic template)
  then dispatches via send_email + save_report (side effects).

The ResearchBrief Pydantic structure is shared: Pipelex produces it, CrewAI consumes it.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crewai import Agent, Crew, Process, Task  # type: ignore[import-untyped]
from crewai.tools import tool  # type: ignore[import-untyped]  # pyright: ignore[reportUnknownVariableType]
from pipelex import pretty_print
from pipelex.pipelex import Pipelex
from pipelex.pipeline.runner import PipelexMTHDSProtocol

from examples.c_advanced.crewai_with_pipelex_tools.structures.research_report__research_brief import ResearchBrief

BUNDLE_DIR = Path(__file__).parent
OUTBOX_FILE = BUNDLE_DIR / "outbox.txt"
REPORTS_DIR = BUNDLE_DIR / "reports"
DOMAIN = "research_report"

# Shared state between tools — typed Pipelex outputs that CrewAI tools can reference.
_session: dict[str, Any] = {}


# ── Pipelex tools ──────────────────────────────────────────────────────────


@tool("run_research")  # pyright: ignore[reportUntypedFunctionDecorator]
def run_research(question: str) -> ResearchBrief:
    """Research a question with fact-checking. Returns a typed ResearchBrief."""
    response = asyncio.run(
        PipelexMTHDSProtocol().execute(
            pipe_code="deep_research",
            inputs={"question": {"concept": f"{DOMAIN}.ResearchQuestion", "content": {"text": question}}},
        )
    )
    brief = response.pipe_output.main_stuff_as(ResearchBrief)
    _session["brief"] = brief
    _session["question"] = question
    return brief


@tool("compose_report")  # pyright: ignore[reportUntypedFunctionDecorator]
def compose_report() -> str:
    """Format the ResearchBrief into a deterministic markdown report via PipeCompose. Call after run_research."""
    brief = _session["brief"]
    question = _session["question"]
    response = asyncio.run(
        PipelexMTHDSProtocol().execute(
            pipe_code="compose_report",
            inputs={
                "brief": {"concept": f"{DOMAIN}.ResearchBrief", "content": brief},
                "question": {"concept": f"{DOMAIN}.ResearchQuestion", "content": {"text": question}},
            },
        )
    )
    report = response.pipe_output.main_stuff_as_str
    _session["report"] = report
    return report


# ── Vanilla CrewAI tools (side effects) ────────────────────────────────────


@tool("send_email")  # pyright: ignore[reportUntypedFunctionDecorator]
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email. Appends to outbox.txt and returns a confirmation."""
    timestamp = datetime.now(timezone.utc).isoformat()
    with OUTBOX_FILE.open("a", encoding="utf-8") as outbox:
        outbox.write(f"--- {timestamp} ---\nTO: {to}\nSUBJECT: {subject}\n\n{body}\n\n")
    return f"Email sent to {to} — subject: {subject!r}"


@tool("save_report")  # pyright: ignore[reportUntypedFunctionDecorator]
def save_report(filename: str, content: str) -> str:
    """Save a report to the reports/ directory. Returns the file path."""
    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / filename
    path.write_text(content, encoding="utf-8")
    return f"Report saved to {path}"


# ── Crew ───────────────────────────────────────────────────────────────────


def main() -> None:
    with Pipelex.make(library_dirs=[str(BUNDLE_DIR)]):
        researcher = Agent(
            role="Researcher",
            goal="Produce a typed ResearchBrief on a given question.",
            backstory="You call run_research with the question and return the typed brief.",
            tools=[run_research],  # pyright: ignore[reportArgumentType]
            verbose=True,
        )
        publisher = Agent(
            role="Publisher",
            goal="Format the research brief into a report, save it, and email it.",
            backstory=(
                "You receive a typed ResearchBrief from the prior task. "
                "First call compose_report to render the deterministic markdown. "
                "Then save it with save_report (filename: report.md). "
                "Then email it with send_email to 'team@example.com' with "
                "a subject derived from the brief's executive_summary."
            ),
            tools=[compose_report, send_email, save_report],  # pyright: ignore[reportArgumentType]
            verbose=True,
        )

        research_task = Task(
            description="Research this question: {question}",
            expected_output="A typed ResearchBrief.",
            agent=researcher,
            output_pydantic=ResearchBrief,
        )
        publish_task = Task(
            description=(
                "1) Call compose_report to get the formatted markdown.\n"
                "2) Save it with save_report (filename: report.md).\n"
                "3) Email it with send_email to 'team@example.com'."
            ),
            expected_output="Confirmation that the report was saved and emailed.",
            agent=publisher,
            context=[research_task],
        )

        result = Crew(
            agents=[researcher, publisher],
            tasks=[research_task, publish_task],
            process=Process.sequential,
            verbose=True,
        ).kickoff(inputs={"question": "What are the tradeoffs of LFP vs NMC batteries for grid storage?"})
        pretty_print(result, title="CrewAI final output")


if __name__ == "__main__":
    main()
