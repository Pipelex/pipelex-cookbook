import asyncio

from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

spec_url_1 = """
https://developer.keap.com/docs/rest/2025-11-05-v1.json
"""


spec_url_2 = """
https://petstore3.swagger.io/api/v3/openapi.json
"""

USE_CASE_1 = (spec_url_1, "extract all the contacts with email pincopalla@gmail.com")
USE_CASE_2 = (spec_url_2, "get me the user with username: johndoe")


async def run_build_function_info(use_case: tuple[str, str]):
    spec_url, operation_to_accomplish = use_case
    return await execute_pipeline(
        pipe_code="build_function_info",
        inputs={
            "openapi_url": {
                "concept": "openapi_function_builder.OpenAPIURL",
                "content": spec_url,
            },
            "operation_to_accomplish": {
                "concept": "openapi_function_builder.OperationToAccomplish",
                "content": operation_to_accomplish,
            },
        },
    )


if __name__ == "__main__":
    # Initialize Pipelex
    Pipelex.make()

    # Run the pipeline
    result = asyncio.run(run_build_function_info(use_case=USE_CASE_2))
