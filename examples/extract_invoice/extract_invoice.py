import asyncio

from pipelex.core.stuffs.document_content import DocumentContent
from pipelex.core.stuffs.list_content import ListContent
from pipelex.hub import get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from examples.extract_invoice.invoice import Invoice
from utils.results_utils import output_result

SAMPLE_NAME = "invoice_extractor"
PDF_URL = "assets/invoice_extractor/invoice_1.pdf"


async def process_invoice(pdf_url: str) -> ListContent[Invoice]:
    pipe_output = await execute_pipeline(
        pipe_code="process_invoice",
        inputs={
            "document": DocumentContent(url=pdf_url),
        },
    )

    return pipe_output.main_stuff_as_list(item_type=Invoice)


if __name__ == "__main__":
    with Pipelex.make(library_dirs=LIBRARY_DIRS):
        # run sample using asyncio
        expense_validations = asyncio.run(process_invoice(pdf_url=PDF_URL))

        # Print the cost reporting
        get_report_delegate().generate_report()

        # Print the flowchart url of the pipeline.

        # Output the results
        output_result(SAMPLE_NAME, "Invoice Extractor", "invoice_extractor.json", expense_validations.rendered_json())
