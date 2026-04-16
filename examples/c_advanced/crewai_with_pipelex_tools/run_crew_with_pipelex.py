"""CrewAI agent that runs an MTHDS pipeline via Pipelex — no re-parsing.

Pipelex owns the `.mthds` bundle (parsing, validation, typed outputs, batching).
CrewAI provides the agent shell and invokes the bundle as a single typed tool.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from crewai import Agent, Crew, Task  # type: ignore[import-untyped]
from crewai.tools import tool  # type: ignore[import-untyped]  # pyright: ignore[reportUnknownVariableType]
from pipelex import pretty_print
from pipelex.pipelex import Pipelex
from pipelex.pipeline.runner import PipelexRunner

from examples.c_advanced.crewai_with_pipelex_tools.structures.research__research_brief import ResearchBrief

BUNDLE_DIR = Path(__file__).parent


@tool("Run the MTHDS research pipeline on a question and return a ResearchBrief.")  # pyright: ignore[reportUntypedFunctionDecorator]
def run_research(question: str) -> ResearchBrief:
    """Gather sources, batch fact-check, and synthesize — all validated by Pipelex."""
    response = asyncio.run(
        PipelexRunner().execute_pipeline(
            pipe_code="deep_research",
            inputs={"question": {"concept": "research.ResearchQuestion", "content": {"text": question}}},
        )
    )
    return response.pipe_output.main_stuff_as(ResearchBrief)


def main() -> None:
    with Pipelex.make(library_dirs=[str(BUNDLE_DIR)]):
        agent = Agent(
            role="Research Director",
            goal="Deliver a rigorous research brief.",
            backstory="You invoke the run_research tool and report its structured output.",
            tools=[run_research],  # pyright: ignore[reportArgumentType]
            verbose=True,
        )
        task = Task(
            description="Research this: {question}",
            expected_output="A ResearchBrief.",
            agent=agent,
            output_pydantic=ResearchBrief,
        )
        result = Crew(agents=[agent], tasks=[task], verbose=True).kickoff(inputs={"question": "LFP vs NMC batteries for grid storage — tradeoffs?"})
        pretty_print(result, title="CrewAI final output")


if __name__ == "__main__":
    main()
