import asyncio

from pipelex import pretty_print
from pipelex.core.stuffs.pdf_content import PDFContent
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline
from pipelex.system.runtime import IntegrationMode

from examples.extract_dpe.extract_dpe_struct import Dpe
from utils.results_utils import output_result

SAMPLE_NAME = "pdf_power_extractor_dpe"
PDF_PATH = "assets/extract_dpe/dpe_single_page.pdf"


async def extract_dpe(pdf_url: str) -> Dpe:
    pipe_output = await execute_pipeline(
        pipe_code="power_extractor_dpe",
        inputs={
            "document": PDFContent(url=pdf_url),
        },
    )
    working_memory = pipe_output.working_memory
    dpe: Dpe = working_memory.get_list_stuff_first_item_as(name="dpe", item_type=Dpe)
    return dpe


# start Pipelex
with Pipelex.make(integration_mode=IntegrationMode.CLI) as pipelex:
    # run sample using asyncio
    dpe = asyncio.run(extract_dpe(pdf_url=PDF_PATH))
    pretty_print(dpe, title="DPE")

    # output results
    output_result(SAMPLE_NAME, "DPE", "dpe.json", dpe.rendered_json())
