import asyncio

from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from pipelex_libraries.pipelines.examples.power_extractor.power_extractor import ProofOfPurchase
from utils.results_utils import get_results_dir_path

SAMPLE_NAME = "pdf_power_extractor_proof_of_purchase"
PDF_PATH = "assets/extract_proof_of_purchase/restaurant_invoice.pdf"


async def power_extractor(pdf_url: str) -> ProofOfPurchase:
    working_memory = WorkingMemoryFactory.make_from_pdf(
        pdf_url=pdf_url,
        concept_code="documents.PDF",
        name="pdf",
    )
    pipe_output, _ = await execute_pipeline(
        pipe_code="power_extractor_proof_of_purchase",
        working_memory=working_memory,
    )
    working_memory = pipe_output.working_memory
    proof_of_purchase: ProofOfPurchase = working_memory.get_list_stuff_first_item_as(name="proof_of_purchase", item_type=ProofOfPurchase)
    return proof_of_purchase


# start Pipelex
Pipelex.make()
# run sample using asyncio
proof_of_purchase = asyncio.run(power_extractor(pdf_url=PDF_PATH))

# output results
output_dir = get_results_dir_path(sample_name=SAMPLE_NAME)
