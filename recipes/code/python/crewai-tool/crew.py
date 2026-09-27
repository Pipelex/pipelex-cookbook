# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["pipelex-sdk==0.12.0", "crewai>=1.15,<2", "httpx>=0.25", "pydantic>=2.10.6", "typing-extensions>=4"]
# ///
"""A CrewAI crew whose reviewer checks a counterparty's NDA against the company's playbook through a Pipelex method, and
whose editor explains the review to the colleague who needs the NDA signed.

The method is the cookbook's NDA review, run by its address as a CrewAI tool that holds the company's playbook. The crew
stays free to decide what to do next, while the review it works from comes out of a fixed pipeline with a typed result:
a verdict, a note for counsel, and one row per position of the playbook with the clause found, the assessment and the
playbook's fallback wording, validated by the `NdaReview` model generated from the method. The memo is rendered by this
script from that typed result: the verdict, the wording to propose and the note for counsel are copied from it, and the
editor writes only the plain-language explanation around them, so no agent can change what the review decided.

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
    """The method as a tool. The playbook is the company's and fixed, so the tool holds it and the agent names only the NDA.
    The tool keeps the typed review it returned, which the script renders the memo's decisive parts from."""

    name: str = "review_nda"
    description: str = (
        "Review a counterparty's NDA, given by its link, against the company's NDA playbook. Returns JSON: a verdict, a note "
        "for counsel, and one row per playbook position with the clause found, what the draft says, the assessment "
        "(acceptable, negotiate, refuse or missing) and the playbook's fallback wording."
    )
    args_schema: type[BaseModel] = ReviewRequest
    # The reviewer's answer is the tool's JSON itself, so the editor explains the very review the memo is rendered from.
    result_as_answer: bool = True
    playbook: str
    review: NdaReview | None = None

    @override
    def _run(self, nda_url: str) -> str:
        self.review = asyncio.run(review_nda(nda_url, playbook=self.playbook))
        return self.review.model_dump_json(indent=2)


ASSESSMENT_LABELS = {"negotiate": "to negotiate", "refuse": "to refuse", "missing": "missing from the draft"}


def quoted(text: str) -> str:
    """The text as a Markdown blockquote, each of its lines kept as it is."""
    return "\n".join(f"> {line}" if line else ">" for line in text.splitlines())


def render_memo(review: NdaReview, *, explanation: str) -> str:
    """The memo: the verdict as the method returned it, the editor's explanation, then every position to change and the note
    for counsel, copied from the typed review, so that the decision and its wording never pass through an agent."""
    lines = ["# NDA review", "", f"**Verdict:** {review.verdict}", "", explanation.strip(), "", "## What to ask for", ""]
    to_change = [position for position in review.positions if position.assessment != "acceptable"]
    if not to_change:
        lines += ["Every position of the playbook is acceptable as the draft stands.", ""]
    for position in to_change:
        where = f" ({position.clause})" if position.clause else ""
        lines += [f"### {position.position}: {ASSESSMENT_LABELS[position.assessment]}", ""]
        lines += [f"**The draft says**{where}: {position.the_draft_says}", ""]
        if position.fallback:
            lines += ["**The playbook asks for:**", "", quoted(position.fallback), ""]
        else:
            lines += ["The playbook gives no wording for this position.", ""]
    lines += ["## Note for counsel", "", quoted(review.note_for_counsel), ""]
    return "\n".join(lines)


def build_crew(review_tool: ReviewNda) -> Crew:
    reviewer = Agent(
        role="Contract reviewer",
        goal="Get the playbook review of the NDA with the review_nda tool, and hand it over unchanged.",
        backstory="You never review a contract from memory: you call review_nda once with the NDA's link and return its JSON.",
        tools=[review_tool],
    )
    editor = Agent(
        role="Editor",
        goal="Explain an NDA review in plain language to the colleague who needs the NDA signed.",
        backstory=(
            "You write plain, short explanations for people who are not lawyers. You add no legal judgment of your own and "
            "write no contract wording: the verdict, the wording to propose and the note for counsel are the review's, and "
            "the memo carries them as the review wrote them."
        ),
    )
    review_task = Task(
        description="Review the NDA at this link against the company's playbook: {nda_url}",
        expected_output="The JSON review returned by review_nda.",
        agent=reviewer,
    )
    explanation_task = Task(
        description=(
            "Write the explanation that opens a memo for the colleague who asked for this NDA, who is not a lawyer. The "
            "review's verdict is set above your explanation, and every position to change, with the playbook's wording, and "
            "the note for counsel are appended below it, all copied verbatim from the review. So write no verdict of your "
            "own and no contract wording, and do not restate the wording: explain in plain language what the review means, "
            "whether the NDA can be signed now, what the changes amount to and why they matter to the company, and what "
            "the colleague should do next."
        ),
        expected_output="Two to four short paragraphs of plain Markdown text, with no heading, no table and no contract wording.",
        agent=editor,
        context=[review_task],
    )
    return Crew(agents=[reviewer, editor], tasks=[review_task, explanation_task], process=Process.sequential)


def main() -> None:
    parser = argparse.ArgumentParser(description="Review an NDA against the company's playbook, and write the memo that goes with it.")
    parser.add_argument("nda_url", nargs="?", default=SAMPLE_NDA_URL, help="A link to the NDA the hosted API can fetch (default: the sample NDA)")
    parser.add_argument("--playbook", type=Path, help="Your NDA playbook, as a text or Markdown file (default: the method's sample playbook)")
    arguments = parser.parse_args()
    playbook = arguments.playbook.read_text(encoding="utf-8") if arguments.playbook else sample_playbook()
    review_tool = ReviewNda(playbook=playbook)
    # CrewAI leaves part of `kickoff`'s signature unannotated, which strict mode reports on every call.
    result = build_crew(review_tool).kickoff(inputs={"nda_url": arguments.nda_url})  # pyright: ignore[reportUnknownMemberType]
    if review_tool.review is None:
        # The memo's verdict, wording and note for counsel come from the method alone, never from an agent's own words.
        sys.exit("the crew finished without review_nda returning a review, so no memo was written")
    memo = render_memo(review_tool.review, explanation=str(result))
    Path("memo.md").write_text(memo, encoding="utf-8")
    print(memo)


if __name__ == "__main__":
    main()
