import asyncio

from pipelex import pretty_print
from pipelex.core.stuffs.document_content import DocumentContent
from pipelex.core.stuffs.list_content import ListContent
from pipelex.core.stuffs.page_content import PageContent
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline
from pipelex.tools.misc.file_utils import save_text_to_path

from examples.constants import LIBRARY_DIRS
from utils.results_utils import get_results_dir_path

SAMPLE_NAME = "simple_ocr"
PDF_URL = "assets/simple_ocr/illustrated_train_article.pdf"


async def simple_ocr(pdf_url: str) -> ListContent[PageContent]:
    pipe_output = await execute_pipeline(
        pipe_code="extract_page_contents_from_pdf",
        inputs={
            "document": DocumentContent(url=pdf_url),
        },
    )
    page_content_list: ListContent[PageContent] = pipe_output.main_stuff_as_list(item_type=PageContent)
    return page_content_list


if __name__ == "__main__":
    with Pipelex.make(library_dirs=LIBRARY_DIRS):
        # run sample using asyncio
        page_content_list = asyncio.run(simple_ocr(pdf_url=PDF_URL))

        # output results
        output_dir = get_results_dir_path(sample_name=SAMPLE_NAME)
        for page_index, page_content in enumerate(page_content_list.items):
            if page_text := page_content.text_and_images.text:
                directory_for_page = f"{output_dir}/page_{page_index}"
                save_text_to_path(page_text.text, directory_for_page)

        # output results
        pretty_print(f"Saved {len(page_content_list.items)} pages to {output_dir}")
