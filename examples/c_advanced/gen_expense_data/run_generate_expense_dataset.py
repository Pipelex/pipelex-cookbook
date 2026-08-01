import sys
from pathlib import Path

# Add script directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
import re

from pipelex.pipelex import Pipelex
from pipelex.pipeline.runner import PipelexMTHDSProtocol
from pipelex.runtime_hub import get_storage_provider
from weasyprint import CSS, HTML

from examples.c_advanced.gen_expense_data.structures.expense_data_generation__employee_expense_report import (
    expense_data_generation__EmployeeExpenseReport,
)
from examples.c_advanced.gen_expense_data.structures.expense_data_generation__nb_of_employees import expense_data_generation__NbOfEmployees

OUTPUT_DIR = Path(__file__).parent / "output"


def to_snake_case(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


async def run_generate_expense_dataset() -> list[expense_data_generation__EmployeeExpenseReport]:
    runner = PipelexMTHDSProtocol()
    response = await runner.execute(
        pipe_code="generate_expense_dataset",
        inputs={
            "nb_employees": {
                "concept": "expense_data_generation.NbOfEmployees",
                "content": expense_data_generation__NbOfEmployees(number=10),
            },
        },
    )
    pipe_output = response.pipe_output
    return pipe_output.main_stuff_as_items(item_type=expense_data_generation__EmployeeExpenseReport)


async def export_single_report(report: expense_data_generation__EmployeeExpenseReport) -> None:
    """Export a single employee expense report to a folder with PDF."""
    # Create folder for employee
    folder = OUTPUT_DIR / report.employee.employee_id
    folder.mkdir(exist_ok=True)

    # Copy receipt images first (needed for PDF generation)
    for item in report.expenses_with_receipts:
        filename = f"{to_snake_case(item.expense.business_purpose)}.png"
        image_path = folder / filename
        image_bytes = await get_storage_provider().load(item.receipt.url)
        image_path.write_bytes(image_bytes)

    # Update HTML to use local image paths
    html_content = report.html_report.inner_html
    for item in report.expenses_with_receipts:
        filename = f"{to_snake_case(item.expense.business_purpose)}.png"
        html_content = html_content.replace(item.receipt.url, filename)

    # Generate PDF from HTML
    HTML(string=html_content, base_url=str(folder)).write_pdf(  # pyright: ignore[reportUnknownMemberType]
        target=folder / "expense_report.pdf", stylesheets=[CSS(string="@page { size: A4; margin: 1.5cm; }")], pdf_variant="pdf/a-3u"
    )


async def export_to_folders(reports: list[expense_data_generation__EmployeeExpenseReport]):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Export all reports in parallel
    await asyncio.gather(*[export_single_report(report) for report in reports])


if __name__ == "__main__":
    with Pipelex.make(library_dirs=["examples/c_advanced/gen_expense_data"]):
        result = asyncio.run(run_generate_expense_dataset())
        asyncio.run(export_to_folders(result))
