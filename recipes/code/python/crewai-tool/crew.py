# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["pipelex-sdk==0.12.0", "crewai>=1.15,<2", "httpx>=0.25", "pydantic>=2.10.6", "typing-extensions>=4"]
# ///
"""A CrewAI crew whose reviewer checks a counterparty's NDA against the company's playbook through a Pipelex method, and
whose editor turns the review into a memo for the colleague who needs the NDA signed.

The method is the cookbook's NDA review, run by its address as a CrewAI tool that holds the company's playbook. The crew
stays free to decide what to do next, while the review it works from comes out of a fixed pipeline with a typed result:
a verdict, a note for counsel, and one row per position of the playbook with the clause found, the assessment and the
playbook's fallback wording, validated by the `NdaReview` model generated from the method.

    uv run crew.py                                   # the method's sample NDA, against its sample playbook
    uv run crew.py <NDA URL> [--playbook <file>]     # an NDA the hosted API can fetch, against your own playbook

`PIPELEX_API_KEY` must be set, and the crew's own agents need a model CrewAI can reach, `OPENAI_API_KEY` by default.
The memo is printed and written to memo.md.
"""

import argparse
import asyncio
import sys
from pathlib import Path

import httpx
from crewai import Agent, Crew, Process, Task
from crewai.tools import BaseTool
from pipelex_sdk.client import PipelexAPIClient
from pydantic import BaseModel, Field
from typing_extensions import override

from generated.review_nda.models import NdaPlaybook, NdaReview

METHOD_REF = "github.com/Pipelex/pipelex-cookbook/review_nda@v0.20.0"
SAMPLE_NDA_URL = "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/v0.20.0/assets/review_nda/mutual_nda.pdf"
SAMPLE_INPUTS_URL = "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/v0.20.0/methods/review_nda/inputs.json"


class PlaybookInput(BaseModel):
    content: NdaPlaybook


class SampleInputs(BaseModel):
    """The part of the method's sample inputs the script reads: the playbook."""

    playbook: PlaybookInput


def sample_playbook() -> str:
    """The method's sample playbook, written for the example, from the inputs its cookbook page links to."""
    return SampleInputs.model_validate(httpx.get(SAMPLE_INPUTS_URL).raise_for_status().json()).playbook.content.text


async def review_nda(nda_url: str, *, playbook: str) -> NdaReview:
    async with PipelexAPIClient() as client:
        results = await client.start_and_wait(
            method_ref=METHOD_REF,
            inputs={"nda": {"url": nda_url}, "playbook": {"concept": "nda_review.NdaPlaybook", "content": {"text": playbook}}},
        )
    print(f"NDA reviewed by run {results.pipeline_run_id}", file=sys.stderr)
    return NdaReview.model_validate(results.main_stuff)


class ReviewRequest(BaseModel):
    nda_url: str = Field(description="The link to the counterparty's NDA, exactly as given, which the hosted API fetches")


class ReviewNda(BaseTool):
    """The method as a tool. The playbook is the company's and fixed, so the tool holds it and the agent names only the NDA."""

    name: str = "review_nda"
    description: str = (
        "Review a counterparty's NDA, given by its link, against the company's NDA playbook. Returns JSON: a verdict, a note "
        "for counsel, and one row per playbook position with the clause found, what the draft says, the assessment "
        "(acceptable, negotiate, refuse or missing) and the playbook's fallback wording."
    )
    args_schema: type[BaseModel] = ReviewRequest
    playbook: str

    @override
    def _run(self, nda_url: str) -> str:
        return asyncio.run(review_nda(nda_url, playbook=self.playbook)).model_dump_json(indent=2)


def build_crew(playbook: str) -> Crew:
    reviewer = Agent(
        role="Contract reviewer",
        goal="Get the playbook review of the NDA with the review_nda tool, and hand it over unchanged.",
        backstory="You never review a contract from memory: you call review_nda once with the NDA's link and return its JSON.",
        tools=[ReviewNda(playbook=playbook)],
    )
    editor = Agent(
        role="Editor",
        goal="Turn an NDA review into a short memo for the colleague who needs the NDA signed.",
        backstory=(
            "You write plain, short memos for people who are not lawyers. You add no legal judgment of your own: every "
            "change you ask for, and the wording you propose for it, comes from the review, and whatever the review sends "
            "to counsel goes to counsel."
        ),
    )
    review_task = Task(
        description="Review the NDA at this link against the company's playbook: {nda_url}",
        expected_output="The JSON review returned by review_nda.",
        agent=reviewer,
    )
    memo_task = Task(
        description=(
            "Write a Markdown memo of at most one page from the review, for the colleague who asked for the NDA: whether "
            "it can be signed now, each position the review does not find acceptable with the playbook's wording to "
            "propose instead, and what goes to counsel and why."
        ),
        expected_output="A Markdown memo of at most one page.",
        agent=editor,
        context=[review_task],
    )
    return Crew(agents=[reviewer, editor], tasks=[review_task, memo_task], process=Process.sequential)


def main() -> None:
    parser = argparse.ArgumentParser(description="Review an NDA against the company's playbook, and write the memo that goes with it.")
    parser.add_argument("nda_url", nargs="?", default=SAMPLE_NDA_URL, help="A link to the NDA the hosted API can fetch (default: the sample NDA)")
    parser.add_argument("--playbook", type=Path, help="Your NDA playbook, as a text or Markdown file (default: the method's sample playbook)")
    arguments = parser.parse_args()
    playbook = arguments.playbook.read_text(encoding="utf-8") if arguments.playbook else sample_playbook()
    # CrewAI leaves part of `kickoff`'s signature unannotated, which strict mode reports on every call.
    result = build_crew(playbook).kickoff(inputs={"nda_url": arguments.nda_url})  # pyright: ignore[reportUnknownMemberType]
    memo = str(result)
    Path("memo.md").write_text(memo, encoding="utf-8")
    print(memo)


if __name__ == "__main__":
    main()
