import asyncio

from pipelex import pretty_print
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.libraries.pipelines.documents import PageContent
from pipelex.pipelex import Pipelex
from pipelex.run import run_pipe_code


async def simple_ocr(page_scan: str):
    working_memory = WorkingMemoryFactory.make_from_pdf(
        pdf_url=page_scan,
        concept_code="documents.PDF",
        name="pdf",
    )
    pipe_output = await run_pipe_code(
        pipe_code="extract_page_contents_from_pdf",
        working_memory=working_memory,
    )
    text_and_image = pipe_output.main_stuff_as_list(item_type=PageContent)

    pretty_print(text_and_image)


PDF_URL = "data/solar_system.pdf"
Pipelex.make()
asyncio.run(
    simple_ocr(
        page_scan=PDF_URL,
    )
)
