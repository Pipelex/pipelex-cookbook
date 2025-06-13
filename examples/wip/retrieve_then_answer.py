import asyncio

from pipelex import pretty_print
from pipelex.core.stuff_factory import StuffFactory
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.hub import get_pipeline_tracker, get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline


def read_text_from_file(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()


async def retrieve_then_answer():
    # Example image path - adjust as needed
    text_path = "assets/retrieve_then_answer/contract.txt"

    text_stuff = StuffFactory.make_from_str(str_value=read_text_from_file(text_path), name="text", concept_code="native.Text")
    question_stuff = StuffFactory.make_from_str(
        str_value="What are the transaction fees for using the WebTech Solutions data processing \
            platform, and how are they calculated?",
        name="question",
        concept_code="answer.Question",
    )
    client_instructions = StuffFactory.make_from_str(
        str_value="If there are multiple fees, take the last one in time.",
        name="client_instructions",
        concept_code="native.Text",
    )

    # Create working memory from image
    working_memory = WorkingMemoryFactory.make_from_multiple_stuffs(stuff_list=[text_stuff, question_stuff, client_instructions])

    # Execute the retrieve_then_answer pipeline
    pipe_output, _ = await execute_pipeline(
        pipe_code="retrieve_then_answer", working_memory=working_memory, dynamic_output_concept_code="contracts.Fees"
    )

    return pipe_output


# Start Pipelex
Pipelex.make()

# Run sample using asyncio
evaluation_result = asyncio.run(retrieve_then_answer())

# Print results
pretty_print(evaluation_result, title="Purchase Document Evaluation")

# Print the cost reporting
get_report_delegate().generate_report()

# Print the flowchart url of the pipeline
get_pipeline_tracker().output_flowchart()
