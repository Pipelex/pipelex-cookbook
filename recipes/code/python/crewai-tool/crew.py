# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["pipelex-sdk==0.12.0", "crewai>=1.15,<2"]
# ///
"""A CrewAI crew whose analyst drafts a research brief through a Pipelex method, and whose editor turns it into a memo.

The method is the cookbook's research report, run by its address as a CrewAI tool. The crew stays free to decide what
to do next, while the brief it works from comes out of a fixed pipeline with a typed result: an executive summary,
key findings and open questions, validated by the `ResearchBrief` model generated from the method. The method drafts
from its model's own knowledge and searches no source, so the editor is told to mark what needs checking.

    uv run crew.py "What are the tradeoffs of LFP versus NMC batteries for grid storage?"

`PIPELEX_API_KEY` must be set, and the crew's own agents need a model CrewAI can reach, `OPENAI_API_KEY` by default.
The memo is printed and written to memo.md.
"""

import asyncio
import sys
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.tools import BaseTool
from pipelex_sdk.client import PipelexAPIClient
from pydantic import BaseModel, Field
from typing_extensions import override

from generated.research_report.models import ResearchBrief

METHOD_REF = "github.com/Pipelex/pipelex-cookbook/research_report@v0.18.0"
# The package's main pipe renders a Markdown report; the tool runs the pipe beneath it, which returns the typed brief.
PIPE_CODE = "research_report.deep_research"
DEFAULT_QUESTION = "What are the tradeoffs of LFP versus NMC batteries for grid storage?"


async def draft_brief(question: str) -> ResearchBrief:
    async with PipelexAPIClient() as client:
        results = await client.start_and_wait(method_ref=METHOD_REF, pipe_code=PIPE_CODE, inputs={"question": question})
    print(f"research brief drafted by run {results.pipeline_run_id}", file=sys.stderr)
    return ResearchBrief.model_validate(results.main_stuff)


class BriefRequest(BaseModel):
    question: str = Field(description="The research question, as one full sentence")


class DraftResearchBrief(BaseTool):
    name: str = "draft_research_brief"
    description: str = (
        "Draft a research brief on a question from a model's own knowledge, looking at it from three angles: "
        "an executive summary, key findings and open questions, as JSON. It searches no source."
    )
    args_schema: type[BaseModel] = BriefRequest

    @override
    def _run(self, question: str) -> str:
        return asyncio.run(draft_brief(question)).model_dump_json(indent=2)


def build_crew() -> Crew:
    analyst = Agent(
        role="Research analyst",
        goal="Get a research brief on the question with the draft_research_brief tool, and hand it over unchanged.",
        backstory="You never answer from memory: you call draft_research_brief once with the question and return its JSON.",
        tools=[DraftResearchBrief()],
    )
    editor = Agent(
        role="Editor",
        goal="Turn a research brief into a one-page memo a decision-maker can act on.",
        backstory=(
            "You write plain, short memos. The briefs you receive were drafted from a model's own knowledge without "
            "searching any source, so you say which findings a reader should verify before relying on them."
        ),
    )
    brief_task = Task(
        description="Draft a research brief on this question: {question}",
        expected_output="The JSON research brief returned by draft_research_brief.",
        agent=analyst,
    )
    memo_task = Task(
        description=(
            "Write a one-page Markdown memo from the research brief: a one-paragraph answer, the three findings that "
            "matter most for a decision, what remains open, and a short list of claims to verify in sources."
        ),
        expected_output="A Markdown memo of at most one page.",
        agent=editor,
        context=[brief_task],
    )
    return Crew(agents=[analyst, editor], tasks=[brief_task, memo_task], process=Process.sequential)


def main() -> None:
    question = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUESTION
    # CrewAI leaves part of `kickoff`'s signature unannotated, which strict mode reports on every call.
    result = build_crew().kickoff(inputs={"question": question})  # pyright: ignore[reportUnknownMemberType]
    memo = str(result)
    Path("memo.md").write_text(memo, encoding="utf-8")
    print(memo)


if __name__ == "__main__":
    main()
