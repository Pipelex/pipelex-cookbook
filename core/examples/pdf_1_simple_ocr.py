import asyncio

from pipelex import pretty_print
from pipelex.core.stuff_content import ListContent, PageContent
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.pipelex import Pipelex
from pipelex.run import run_pipe_code

from utils.results_utils import get_results_dir_path

SAMPLE_NAME = "pdf_1_simple_ocr"
PDF_URL = "assets/illustrated_train_article.pdf"


async def simple_ocr(pdf_url: str):
    working_memory = WorkingMemoryFactory.make_from_pdf(
        pdf_url=pdf_url,
        concept_code="documents.PDF",
        name="pdf",
    )
    pipe_output = await run_pipe_code(
        pipe_code="extract_page_contents_from_pdf",
        working_memory=working_memory,
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
