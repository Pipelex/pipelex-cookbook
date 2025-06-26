import asyncio

from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from pipelex_libraries.pipelines.examples.extract_dpe.extract_dpe import Dpe
from utils.results_utils import get_results_dir_path

SAMPLE_NAME = "pdf_power_extractor_dpe"
PDF_PATH = "assets/extract_dpe/dpe_single_page.pdf"


async def extract_dpe(pdf_url: str) -> Dpe:
    working_memory = WorkingMemoryFactory.make_from_pdf(
        pdf_url=pdf_url,
        concept_str="PDF",
        name="pdf",
    )
    pipe_output = await execute_pipeline(
        pipe_code="power_extractor_dpe",
        working_memory=working_memory,
    )
    working_memory = pipe_output.working_memory
    dpe: Dpe = working_memory.get_list_stuff_first_item_as(name="dpe", item_type=Dpe)
    return dpe


# start Pipelex
Pipelex.make()
# run sample using asyncio
dpe = asyncio.run(extract_dpe(pdf_url=PDF_PATH))

# output results
output_dir = get_results_dir_path(sample_name=SAMPLE_NAME)
