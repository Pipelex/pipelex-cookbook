import asyncio
from typing import Optional

from pipelex import pretty_print
from pipelex.core.stuff_content import PageContent
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.pipelex import Pipelex
from pipelex.run import run_pipe_code


async def simple_ocr(page_scan: str, export_dir: Optional[str] = None):
    working_memory = WorkingMemoryFactory.make_from_pdf(
        pdf_url=page_scan,
        concept_code="documents.PDF",
        name="pdf",
    )
    pipe_output = await run_pipe_code(
        pipe_code="extract_page_contents_from_pdf",
        working_memory=working_memory,
        params={"export_dir": export_dir} if export_dir else None,
    )
    text_and_image = pipe_output.main_stuff_as_list(item_type=PageContent)

    pretty_print(text_and_image)


async def main():
    PDF_URL = "data/illustrated_train_article.pdf"
    Pipelex.make()
    # TODO: Use ActivityHandlerForResultFiles for exporting results
    await simple_ocr(
        page_scan=PDF_URL,
        export_dir="results/ocr/illustrated_train_article/",
    )


if __name__ == "__main__":
    asyncio.run(main())
