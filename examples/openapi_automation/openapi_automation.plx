domain = "openapi_automation"
description = "Building function info from OpenAPI JSON spec"
main_pipe = "build_function_info"

[concept]
OpenAPISpec = "Structured OpenAPI specification for the backend."
FunctionInfo = "Information about a function in the OpenAPI spec."
FunctionChoice = "Choice of OpenAPI function to accomplish an operation."
RequestDetails = "Request Details containing actual values for the request"

[concept.OpenAPIURL]
description = "The URL of the OpenAPI JSON spec"
refines = "Text"

[concept.OperationToAccomplish]
description = "The specific operation to accomplish."
refines = "Text"

[concept.RelevantOpenapiPaths]
description = """
Relevant information (e.g., paths, methods) from the OpenAPI JSON specification that pertains to the operation to accomplish.
"""

[concept.RelevantOpenapiPaths.structure]
paths = { type = "text", description = "List of relevant paths.", required = true }
methods = { type = "text", description = "List of relevant methods.", required = true }

[concept.FunctionName]
description = "The name of the function."
refines = "Text"

[concept.FunctionParameter]
description = "The necessary function parameters."

[concept.FunctionParameter.structure]
name = { type = "text", description = "Name of a function parameter.", required = true }
type = { type = "text", description = "Data type of a function parameter.", required = true }
value = { type = "text", description = "Values of each function parameter.", required = true }

[concept.ApiResponseResult]
description = "The compiled api response content."

[concept.ApiResponseResult.structure]
response = { type = "text", description = "The response of the api server", required = true }


[pipe.build_function_info]
type = "PipeSequence"
description = """
Main pipeline that builds the function name and function parameters and values necessary for the task based on the OpenAPI JSON spec and the operation to accomplish.
"""
inputs = { openapi_url = "OpenAPIURL", operation_to_accomplish = "OperationToAccomplish" }
output = "ApiResponseResult"
#output = "FunctionDetails"
steps = [
    { pipe = "obtain_api_spec", result = "openapi_spec"},
    { pipe = "extract_available_functions", result = "function_info" },
    { pipe = "choose_function", result = "function_choice" },
    { pipe = "get_function_details", result = "function_details" },
    { pipe = "prepare_request", result = "request_details"},
    { pipe = "execute_api_call", result = "result_api_call" },
]

[pipe.obtain_api_spec]
type = "PipeFunc"
description = "Obtains the OpenAPI spec given a URL."
inputs = { openapi_url = "OpenAPIURL" }
output = "OpenAPISpec"
function_name = "obtain_openapi_model"

[pipe.extract_available_functions]
type = "PipeFunc"
description = "Extracts the available functions from the OpenAPI spec."
inputs = { openapi_url = "OpenAPIURL" }
output = "FunctionInfo[]"
function_name = "extract_available_functions"


[pipe.choose_function]
type = "PipeLLM"
description = "Uses the operation to accomplish and relevant OpenAPI paths to determine the function name."
inputs = { operation_to_accomplish = "OperationToAccomplish", function_info = "FunctionInfo[]" }
output = "FunctionChoice"
model = "llm_to_engineer"
system_prompt = """
Determine a function name based on the operation to accomplish and relevant OpenAPI paths. Be concise.
"""
prompt = """
Based on the operation to accomplish and the available OpenAPI functions, choose the relevant function name.

@operation_to_accomplish

@function_info
"""

[pipe.get_function_details]
type = "PipeFunc"
description = "Gets the details of a function from the OpenAPI spec."
inputs = { function_choice = "FunctionChoice" }
output = "FunctionDetails"
function_name = "get_function_details"



[pipe.prepare_request]
type = "PipeLLM"
description = "Prepares the request body corresponding to the actual request"
inputs = {  operation_to_accomplish = "OperationToAccomplish", function_details = "FunctionDetails" }
output = "RequestDetails"
model = "llm_to_engineer"
prompt = """
Based on the operation to accomplish and the available OpenAPI functions, fill in the actual values for the current request.

@operation_to_accomplish

@function_details

"""


[pipe.execute_api_call]
type = "PipeFunc"
description = "Execute the API request given a CompiledFunctionInfo."
inputs = { request_details = "RequestDetails" }
output = "ApiResponseResult"
function_name = "invoke_function_api_backend"


