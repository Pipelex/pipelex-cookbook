import asyncio

from pipelex import pretty_print
from pipelex.core.stuffs.document_content import DocumentContent
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from examples.constants import LIBRARY_DIRS
from examples.extract_dpe.extract_dpe_struct import Dpe
from utils.results_utils import output_result

SAMPLE_NAME = "extract_dpe"
PDF_PATH = "assets/extract_dpe/dpe_single_page.pdf"


async def extract_dpe(pdf_url: str) -> Dpe:
    pipe_output = await execute_pipeline(
        pipe_code="power_extractor_dpe",
        inputs={
            "document": DocumentContent(url=pdf_url),
        },
    )
    working_memory = pipe_output.working_memory
    dpe: Dpe = working_memory.main_stuff_as(content_type=Dpe)
    pretty_print(dpe, title="DPE")

    # output results
    output_result(
        sample_name=SAMPLE_NAME,
        title="DPE",
        file_name="dpe.json",
        content=dpe.rendered_json(),
    )

    return dpe


if __name__ == "__main__":
    with Pipelex.make(library_dirs=LIBRARY_DIRS):
        # run sample using asyncio
        dpe = asyncio.run(extract_dpe(pdf_url=PDF_PATH))
