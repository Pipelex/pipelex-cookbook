import asyncio

from pipelex import pretty_print
from pipelex.core.stuffs.pdf_content import PDFContent
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline
from pipelex_libraries.pipelines.examples.extract_proof_of_purchase.models import ProofOfPurchase

from utils.results_utils import get_results_dir_path

SAMPLE_NAME = "pdf_power_extractor_proof_of_purchase"
PDF_PATH = "assets/extract_proof_of_purchase/restaurant_invoice.pdf"


async def extract_proof_of_purchase(pdf_url: str) -> ProofOfPurchase:
    pipe_output = await execute_pipeline(
        pipe_code="power_extractor_proof_of_purchase",
        input_memory={
            "document": PDFContent(url=pdf_url),
        },
    )
    working_memory = pipe_output.working_memory
    proof_of_purchase: ProofOfPurchase = working_memory.get_list_stuff_first_item_as(name="proof_of_purchase", item_type=ProofOfPurchase)
    return proof_of_purchase


# start Pipelex
Pipelex.make()
# run sample using asyncio
proof_of_purchase = asyncio.run(extract_proof_of_purchase(pdf_url=PDF_PATH))
pretty_print(proof_of_purchase, title="Proof of Purchase")

# output results
output_dir = get_results_dir_path(sample_name=SAMPLE_NAME)
