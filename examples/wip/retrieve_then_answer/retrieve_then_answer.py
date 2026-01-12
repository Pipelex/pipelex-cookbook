import asyncio

from pipelex import pretty_print
from pipelex.hub import get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline
from pipelex.tools.misc.file_utils import load_text_from_path

TEXT_PATH = "assets/retrieve_then_answer/contract.txt"
QUESTION = """
What are the transaction fees for using the WebTech Solutions data processing platform,
and how are they calculated?
"""
CLIENT_INSTRUCTIONS = "If there are multiple fees, take the last one in time."


def read_text_from_file(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()


async def retrieve_then_answer(text_path: str, question: str, client_instructions: str):
    pipe_output = await execute_pipeline(
        pipe_code="retrieve_then_answer",
        dynamic_output_concept_code="contracts.Fees",
        inputs={
            "text": load_text_from_path(path=text_path),
            "question": {
                "concept": "answer.Question",
                "content": question,
            },
            "client_instructions": client_instructions,
        },
    )

    return pipe_output


# start Pipelex
with Pipelex.make():
    # Run sample using asyncio
    evaluation_result = asyncio.run(
        retrieve_then_answer(
            text_path=TEXT_PATH,
            question=QUESTION,
            client_instructions=CLIENT_INSTRUCTIONS,
        )
    )

    # Print results
    pretty_print(evaluation_result, title="Purchase Document Evaluation")

    # Print the cost reporting
    get_report_delegate().generate_report()

    # Print the flowchart url of the pipeline
