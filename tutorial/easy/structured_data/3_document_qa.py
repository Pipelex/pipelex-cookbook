import asyncio

from pipelex import pretty_print
from pipelex.core.stuffs.document_content import DocumentContent
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from tutorial.easy.structured_data.structured_objects_struct import Answer

LIBRARY_DIRS = ["tutorial"]

# Sample PDF for the demo
SAMPLE_PDF_URL = "assets/simple_ocr/illustrated_train_article.pdf"


async def main():
    question = "What is the main topic of this document?"

    print(f"Document: {SAMPLE_PDF_URL}")
    print(f"Question: {question}")
    print()

    pipe_output = await execute_pipeline(
        pipe_code="document_qa",
        inputs={
            "document": DocumentContent(url=SAMPLE_PDF_URL),
            "question": question,
        },
    )

    answer = pipe_output.main_stuff_as(content_type=Answer)

    pretty_print(f"Answer: {answer.answer}", title="Document Q&A Result")
    print(f"Confidence: {answer.confidence}")
    print(f"Source Quote: {answer.source_quote}")


if __name__ == "__main__":
    with Pipelex.make(library_dirs=LIBRARY_DIRS):
        asyncio.run(main())
