import sys
from pathlib import Path

# Add script directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

import asyncio

from pipelex import pretty_print
from pipelex.core.stuffs.document_content import DocumentContent
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline


async def validate_expense_report_from_pdf(pdf_path: str) -> None:
    """
    Validates an expense report from a PDF document.

    This demonstrates the validation method:
    1. Extract content from the PDF document
    2. Parse the content into a structured EmployeeExpenseReport
    3. Validate each expense against company policies
    4. Display validation results showing approved/rejected expenses

    Args:
        pdf_path: Path to the expense report PDF file
    """
    print(f"\n{'=' * 60}")
    print(f"Validating expense report from: {pdf_path}")
    print(f"{'=' * 60}\n")

    validation_output = await execute_pipeline(
        pipe_code="validate_expense_report",
        inputs={
            "document": DocumentContent(url=pdf_path),
        },
    )

    validation_text = validation_output.main_stuff_as_str
    pretty_print(validation_text, title="Expense Report Validation Result")


if __name__ == "__main__":
    # Example usage with a PDF file
    # Replace with actual path to an expense report PDF
    PDF_PATH = "assets/expense_reports/sample_expense_report.pdf"

    with Pipelex.make(library_dirs=["examples/c_advanced/gen_expense_data"]):
        asyncio.run(validate_expense_report_from_pdf(pdf_path=PDF_PATH))
