"""CrewAI crew mixing a Pipelex-backed agent with a vanilla CrewAI agent.

Agent 1 (Review Analyst) calls the Pipelex tool `analyze_review`, which runs a
validated MTHDS pipeline and returns a typed ReviewAnalysis.
Agent 2 (Customer Support Rep) has no Pipelex tool. It uses a `send_email` tool
(a side effect Pipelex intentionally does not do) to dispatch a reply to the
customer, using the structured analysis as context.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from crewai import Agent, Crew, Process, Task  # type: ignore[import-untyped]
from crewai.tools import tool  # type: ignore[import-untyped]  # pyright: ignore[reportUnknownVariableType]
from pipelex import pretty_print
from pipelex.pipelex import Pipelex
from pipelex.pipeline.runner import PipelexRunner

BUNDLE_DIR = Path(__file__).parent
OUTBOX_FILE = BUNDLE_DIR / "outbox.txt"

SAMPLE_REVIEW = """
I bought the Model X coffee grinder last month. The grind consistency is incredible —
best espresso at home I've ever had. But the hopper is tiny (like 150g max) and the lid
rattles every time. Also would kill for a Bluetooth app so I can adjust settings from
my phone. Otherwise, 5/5, would recommend.
"""


@tool("prepare_customer_email")  # pyright: ignore[reportUntypedFunctionDecorator]
def prepare_customer_email(review: str) -> str:
    """Analyze a review and return a ready-to-send customer email body (deterministic template). Argument `review` is the raw text."""
    response = asyncio.run(
        PipelexRunner().execute_pipeline(
            pipe_code="prepare_customer_email",
            inputs={"review": {"concept": "review.ProductReview", "content": {"text": review}}},
        )
    )
    return response.pipe_output.main_stuff_as_str


@tool("send_email")  # pyright: ignore[reportUntypedFunctionDecorator]
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a customer. Appends the message to outbox.txt and returns a confirmation."""
    timestamp = datetime.now(timezone.utc).isoformat()
    with OUTBOX_FILE.open("a", encoding="utf-8") as outbox:
        outbox.write(f"--- {timestamp} ---\nTO: {to}\nSUBJECT: {subject}\n\n{body}\n\n")
    return f"Email sent to {to} — subject: {subject!r}"


def main() -> None:
    with Pipelex.make(library_dirs=[str(BUNDLE_DIR)]):
        email_prep_agent = Agent(
            role="Email Prep",
            goal="Prepare a ready-to-send customer email body from a product review.",
            backstory="You invoke the prepare_customer_email tool and pass the returned email body to the next agent.",
            tools=[prepare_customer_email],  # pyright: ignore[reportArgumentType]
            verbose=True,
        )
        dispatcher = Agent(
            role="Email Dispatcher",
            goal="Send the prepared email via the send_email tool.",
            backstory="You receive a ready-to-send email body from the prior task and dispatch it via send_email.",
            tools=[send_email],  # pyright: ignore[reportArgumentType]
            verbose=True,
        )

        prep_task = Task(
            description=f"Prepare a customer email for this product review:\n{SAMPLE_REVIEW}",
            expected_output="The email body string.",
            agent=email_prep_agent,
        )
        dispatch_task = Task(
            description=(
                "Send the email body from the prior task via the send_email tool to 'customer@example.com' "
                "with subject 'Thanks for your review'. Pass the body through verbatim — do not rewrite it."
            ),
            expected_output="The confirmation string returned by the send_email tool.",
            agent=dispatcher,
            context=[prep_task],
        )

        result = Crew(
            agents=[email_prep_agent, dispatcher],
            tasks=[prep_task, dispatch_task],
            process=Process.sequential,
            verbose=True,
        ).kickoff()
        pretty_print(result, title="CrewAI final output")
        if OUTBOX_FILE.exists():
            pretty_print(OUTBOX_FILE.read_text(encoding="utf-8"), title=f"{OUTBOX_FILE.name} (side effect)")


if __name__ == "__main__":
    main()
