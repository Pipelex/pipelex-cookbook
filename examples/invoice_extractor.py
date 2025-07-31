import asyncio

from pipelex import pretty_print
from pipelex.core.stuff_content import ListContent, PDFContent
from pipelex.hub import get_pipeline_tracker, get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from pipelex_libraries.pipelines.examples.invoice_extractor.invoice import Invoice

SAMPLE_NAME = "invoice_extractor"
PDF_URL = "assets/invoice_extractor/invoice_1.pdf"


async def process_invoice(pdf_url: str) -> ListContent[Invoice]:
    pipe_output = await execute_pipeline(
        pipe_code="process_invoice",
        input_memory={
            "ocr_input": PDFContent(url=pdf_url),
        },
    )

    return pipe_output.main_stuff_as_list(item_type=Invoice)


# start Pipelex
Pipelex.make()

# run sample using asyncio
expense_validations = asyncio.run(process_invoice(pdf_url=PDF_URL))

# Print results
pretty_print(expense_validations, title="Expense validations")

# Print the cost reporting
get_report_delegate().generate_report()

# Print the flowchart url of the pipeline.
get_pipeline_tracker().output_flowchart()
