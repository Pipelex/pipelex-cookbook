import asyncio

from pipelex import pretty_print
from pipelex.core.stuff_content import ListContent
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.hub import get_pipeline_tracker, get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from pipelex_libraries.pipelines.examples.invoice_extractor.invoice import Invoice


def read_text_file(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()


async def process_expense_report() -> ListContent[Invoice]:
    invoice_pdf_path = "assets/invoice_extractor/invoice_1.pdf"

    # Create Stuff objects
    working_memory = WorkingMemoryFactory.make_from_pdf(
        pdf_url=invoice_pdf_path,
        name="invoice_pdf",
    )
    pipe_output = await execute_pipeline(
        pipe_code="process_invoice",
        working_memory=working_memory,
    )

    return pipe_output.main_stuff_as_list(item_type=Invoice)


# start Pipelex
Pipelex.make()

# run sample using asyncio
expense_validations = asyncio.run(process_expense_report())

# Print results
pretty_print(expense_validations, title="Expense validations")

# Print the cost reporting
get_report_delegate().generate_report()

# Print the flowchart url of the pipeline.
get_pipeline_tracker().output_flowchart()
