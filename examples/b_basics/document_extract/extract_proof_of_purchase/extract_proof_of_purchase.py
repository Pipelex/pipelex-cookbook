import asyncio

from pipelex import pretty_print
from pipelex.core.stuffs.document_content import DocumentContent
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from examples.b_basics.document_extract.extract_proof_of_purchase.models import ProofOfPurchase
from examples.constants import LIBRARY_DIRS
from utils.results_utils import output_result

SAMPLE_NAME = "pdf_power_extractor_proof_of_purchase"
PDF_PATH = "assets/extract_proof_of_purchase/restaurant_invoice.pdf"


async def extract_proof_of_purchase(pdf_url: str) -> ProofOfPurchase:
    pipe_output = await execute_pipeline(
        pipe_code="power_extractor_proof_of_purchase",
        inputs={
            "document": DocumentContent(url=pdf_url),
        },
    )
    working_memory = pipe_output.working_memory
    proof_of_purchase: ProofOfPurchase = working_memory.get_list_stuff_first_item_as(name="proof_of_purchase", item_type=ProofOfPurchase)
    return proof_of_purchase


if __name__ == "__main__":
    with Pipelex.make(library_dirs=LIBRARY_DIRS):
        # run sample using asyncio
        proof_of_purchase = asyncio.run(extract_proof_of_purchase(pdf_url=PDF_PATH))
        pretty_print(proof_of_purchase, title="Proof of Purchase")

        output_result(
            sample_name=SAMPLE_NAME,
            title="Proof of Purchase",
            file_name="proof_of_purchase.json",
            content=proof_of_purchase.rendered_json(),
        )
