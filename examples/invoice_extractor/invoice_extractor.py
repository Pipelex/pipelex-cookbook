import asyncio

from pipelex import pretty_print
from pipelex.core.stuffs.list_content import ListContent
from pipelex.core.stuffs.pdf_content import PDFContent
from pipelex.hub import get_pipeline_tracker, get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from examples.invoice_extractor.invoice import Invoice
from utils.results_utils import output_result

SAMPLE_NAME = "invoice_extractor"
PDF_URL = "assets/invoice_extractor/invoice_1.pdf"


async def process_invoice(pdf_url: str) -> ListContent[Invoice]:
    pipe_output = await execute_pipeline(
        pipe_code="process_invoice",
        inputs={
            "document": PDFContent(url=pdf_url),
        },
    )

    return pipe_output.main_stuff_as_list(item_type=Invoice)


# start Pipelex
Pipelex.make()

# run sample using asyncio
expense_validations = asyncio.run(process_invoice(pdf_url=PDF_URL))

# Print the cost reporting
get_report_delegate().generate_report()

# Print the flowchart url of the pipeline.
get_pipeline_tracker().output_flowchart()

# Output the results
output_result(SAMPLE_NAME, "Invoice Extractor", "invoice_extractor.json", expense_validations.rendered_json())
