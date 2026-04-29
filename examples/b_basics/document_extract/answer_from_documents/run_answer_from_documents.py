import asyncio

from pipelex import pretty_print
from pipelex.core.stuffs.document_content import DocumentContent
from pipelex.core.stuffs.text_content import TextContent
from pipelex.pipelex import Pipelex
from pipelex.pipeline.runner import PipelexRunner

from examples.b_basics.document_extract.answer_from_documents.structures.document_qa__reference_count import ReferenceCount


async def run_answer_from_documents() -> ReferenceCount:
    runner = PipelexRunner()
    response = await runner.execute_pipeline(
        pipe_code="answer_from_documents",
        dynamic_output_concept_ref="document_qa.ReferenceCount",
        inputs={
            "documents": {
                "concept": "native.Document",
                "content": [
                    DocumentContent(
                        url="https://huggingface.co/datasets/yubo2333/MMLongBench-Doc/resolve/main/documents/PH_2016.06.08_Economy-Final.pdf"
                    )
                ],
            },
            "question": {
                "concept": "native.Text",
                "content": TextContent(text="Among all 12 references in this report, how many are from its own research center?"),
            },
            "context": {
                "concept": "native.Text",
                "content": TextContent(text=""),
            },
        },
    )
    return response.pipe_output.main_stuff_as(content_type=ReferenceCount)


if __name__ == "__main__":
    with Pipelex.make(library_dirs=["examples/b_basics/document_extract/answer_from_documents"]):
        result = asyncio.run(run_answer_from_documents())
        pretty_print(result, title="ReferenceCount")
