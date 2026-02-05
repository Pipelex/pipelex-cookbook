import sys
from pathlib import Path

# Add script directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

import asyncio

from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline
from weasyprint import CSS, HTML

from examples.c_advanced.gen_expense_data.structures.expense_data_generation__employee_expense_report import EmployeeExpenseReport
from examples.c_advanced.gen_expense_data.structures.expense_data_generation__nb_of_employees import NbOfEmployees

OUTPUT_DIR = Path(__file__).parent / "output"


async def run_generate_expense_dataset() -> list[EmployeeExpenseReport]:
    pipe_output = await execute_pipeline(
        pipe_code="generate_expense_dataset",
        inputs={
            "nb_employees": {
                "concept": "expense_data_generation.NbOfEmployees",
                "content": NbOfEmployees(number=5),
            },
        },
    )
    return pipe_output.main_stuff_as_items(item_type=EmployeeExpenseReport)


def copy_image(url: str, filepath: Path):
    # pipelex-storage:// maps to .pipelex/storage/
    if url.startswith("pipelex-storage://"):
        local_path = Path(".pipelex/storage") / url.replace("pipelex-storage://", "")
        if local_path.exists():
            filepath.write_bytes(local_path.read_bytes())


async def export_to_folders(reports: list[EmployeeExpenseReport]):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for report in reports:
        # Create folder for employee
        folder = OUTPUT_DIR / report.employee.employee_id
        folder.mkdir(exist_ok=True)

        # Copy receipt images first (needed for PDF generation)
        for item in report.expenses_with_receipts:
            image_path = folder / f"{item.expense.expense_id}.png"
            copy_image(item.receipt_url, image_path)

        # Update HTML to use local image paths
        html_content = report.html_report.inner_html
        for item in report.expenses_with_receipts:
            html_content = html_content.replace(item.receipt_url, f"{item.expense.expense_id}.png")

        # Generate PDF from HTML
        HTML(string=html_content, base_url=str(folder)).write_pdf(  # pyright: ignore[reportUnknownMemberType]
            target=folder / "expense_report.pdf", stylesheets=[CSS(string="@page { size: A4; margin: 1.5cm; }")], pdf_variant="pdf/a-3u"
        )


if __name__ == "__main__":
    with Pipelex.make(library_dirs=["examples/c_advanced/gen_expense_data"]):
        result = asyncio.run(run_generate_expense_dataset())
        asyncio.run(export_to_folders(result))
