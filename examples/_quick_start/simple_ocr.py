import asyncio

from pipelex import pretty_print
from pipelex.core.stuffs.list_content import ListContent
from pipelex.core.stuffs.page_content import PageContent
from pipelex.core.stuffs.pdf_content import PDFContent
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from utils.results_utils import get_results_dir_path

SAMPLE_NAME = "simple_ocr"
PDF_URL = "assets/simple_ocr/illustrated_train_article.pdf"


async def simple_ocr(pdf_url: str) -> ListContent[PageContent]:
    pipe_output = await execute_pipeline(
        pipe_code="extract_page_contents_from_pdf",
        inputs={
            "document": PDFContent(url=pdf_url),
        },
    )
    page_content_list: ListContent[PageContent] = pipe_output.main_stuff_as_list(item_type=PageContent)
    return page_content_list


# start Pipelex
Pipelex.make()

# run sample using asyncio
page_content_list = asyncio.run(simple_ocr(pdf_url=PDF_URL))

# output results
pretty_print(page_content_list)
output_dir = get_results_dir_path(sample_name=SAMPLE_NAME)
for page_index, page_content in enumerate(page_content_list.items):
    directory_for_page = f"{output_dir}/page_{page_index}"
    page_content.save_to_directory(directory=directory_for_page)
