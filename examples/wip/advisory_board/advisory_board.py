import asyncio
from typing import Tuple

from pipelex import pretty_print
from pipelex.hub import get_pipeline_tracker, get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline
from pipelex_libraries.pipelines.wip.advisory_board.advisory_orchestrator import StrategicReport

from utils.results_utils import output_result

SAMPLE_NAME = "advisory_orchestrator"

# Sample business problem
SAMPLE_BUSINESS_PROBLEM = """
We're a mid-stage B2B SaaS company (50 employees, $5M ARR) facing declining customer retention. 
Our churn rate has increased from 8% to 15% annually over the past 6 months. 

Key challenges:
- Customer onboarding takes 4-6 weeks (industry average is 2-3 weeks)
- Support response time averages 24 hours
- Feature adoption is low - only 30% of customers use our advanced features
- Competition from 3 new entrants with better UX

Our goal is to reduce churn to under 10% within 6 months while maintaining growth targets.
We have a budget of $500K and need to prioritize initiatives that will have the biggest impact.

Current team: 8 engineers, 4 sales, 3 marketing, 2 customer success, 5 operations.
Key stakeholders: CEO, VP Product, VP Sales, Head of Customer Success.
"""


async def run_advisory_orchestrator(problem_description: str) -> Tuple[StrategicReport, str]:
    """
    Run the Master Advisory Orchestrator pipeline on a business problem.

    Args:
        problem_description: Description of the business problem to analyze

    Returns:
        Tuple[StrategicReport, str]: A tuple containing:
            - StrategicReport: Comprehensive strategic analysis and recommendations
            - str: Strategic report in markdown format
    """
    print("🚀 Running Master Advisory Orchestrator\n")

    pipe_output = await execute_pipeline(
        pipe_code="master_advisory_orchestrator",
        input_memory={
            "user_input": problem_description,
        },
    )

    # Output the result
    strategic_report = pipe_output.working_memory.get_stuff_as(name="strategic_report", content_type=StrategicReport)
    strategic_report_markdown = pipe_output.main_stuff_as_str
    return strategic_report, strategic_report_markdown


# Start Pipelex
Pipelex.make()

# Run the advisory orchestrator
strategic_report, strategic_report_markdown = asyncio.run(run_advisory_orchestrator(SAMPLE_BUSINESS_PROBLEM))

# Display the strategic report
pretty_print(strategic_report, title="Master Advisory Orchestrator - Strategic Report (json)")
pretty_print(strategic_report_markdown, title="Master Advisory Orchestrator - Strategic Report (markdown)")

# Display cost report (tokens used and cost)
get_report_delegate().generate_report()

# Output pipeline flowchart
get_pipeline_tracker().output_flowchart()

output_result(
    sample_name=SAMPLE_NAME,
    title="Master Advisory Orchestrator - Strategic Report (markdown)",
    file_name="strategic_report.md",
    content=strategic_report_markdown,
)
