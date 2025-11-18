import json
from typing import List
from urllib.parse import urlparse

import requests
from openapiclient import OpenAPIClient
from pipelex.core.memory.working_memory import WorkingMemory
from pipelex.core.stuffs.list_content import ListContent
from pipelex.core.stuffs.text_content import TextContent
from pipelex.system.registries.func_registry import pipe_func

from examples.openapi_automation.models import FunctionChoice, FunctionDetails, FunctionInfo, OpenAPISpec, ParameterDetail, RequestDetails


@pipe_func()
async def invoke_function_api_backend(working_memory: WorkingMemory) -> TextContent:
    """
    Execute an API request using the RequestDetails struct.
    Builds and performs the actual HTTP request using the requests library.
    """
    # Get the base URL from the OpenAPI spec
    openapi_url = working_memory.get_stuff_as_text("openapi_url").text.strip()
    request_details = working_memory.get_stuff_as("request_details", RequestDetails)

    # Get the base URL from the OpenAPI spec
    response = requests.get(url=openapi_url)
    spec_data = response.json()

    # Extract base URL from servers
    base_url = None
    if "servers" in spec_data and len(spec_data["servers"]) > 0:
        base_url = spec_data["servers"][0].get("url", "")

    if not base_url or base_url == "":
        raise ValueError("No server URL found in OpenAPI specification")

    # Validate that base_url is a proper URL with protocol and host
    parsed_url = urlparse(base_url)
    if not parsed_url.scheme:
        raise ValueError(f"Base URL missing protocol (http/https): {base_url}")
    if not parsed_url.netloc:
        raise ValueError(f"Base URL missing host: {base_url}")
    if parsed_url.scheme not in ["http", "https"]:
        raise ValueError(f"Base URL protocol must be http or https, got: {parsed_url.scheme}")

    print(f"Base URL: {base_url}")
    print(f"  Protocol: {parsed_url.scheme}")
    print(f"  Host: {parsed_url.hostname}")
    print(f"  Port: {parsed_url.port if parsed_url.port else 'default'}")
    # Build the full URL with path parameters
    url_path = request_details.path
    if request_details.path_parameters:
        for param_name, param_value in request_details.path_parameters.items():
            url_path = url_path.replace(f"{{{param_name}}}", str(param_value))

    full_url = f"{base_url.rstrip('/')}/{url_path.lstrip('/')}"

    # Prepare request components
    headers = {}
    if request_details.header_parameters:
        headers.update(request_details.header_parameters)

    cookies = {}
    if request_details.cookie_parameters:
        cookies.update(request_details.cookie_parameters)

    params = {}
    if request_details.query_parameters:
        params.update(request_details.query_parameters)

    # Prepare request body
    json_body = None
    if request_details.request_body:
        json_body = request_details.request_body

    # Execute the HTTP request
    print(f"Executing {request_details.http_method} request to {full_url}")
    print(f"Query params: {params}")
    print(f"Headers: {headers}")
    print(f"Body: {json_body}")

    try:
        http_response = requests.request(
            method=request_details.http_method,
            url=full_url,
            params=params if params else None,
            headers=headers if headers else None,
            cookies=cookies if cookies else None,
            json=json_body if json_body else None,
        )

        # Raise an exception for HTTP errors
        http_response.raise_for_status()

        # Try to parse JSON response, fallback to text
        try:
            result = http_response.json()
            return TextContent(text=json.dumps(result, indent=2))
        except json.JSONDecodeError:
            return TextContent(text=http_response.text)

    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        if hasattr(e, "response") and e.response is not None:
            error_msg += f"\nStatus code: {e.response.status_code}"
            error_msg += f"\nResponse: {e.response.text}"
        print(error_msg)
        return TextContent(text=error_msg)


@pipe_func()
async def obtain_openapi_spec(working_memory: WorkingMemory) -> TextContent:
    openapi_url = working_memory.get_stuff_as_text("openapi_url").text.strip()
    response = requests.get(url=openapi_url)
    spec_data = response.json()

    api = OpenAPIClient(definition=openapi_url)

    # Use the async client with context manager
    async with api.AsyncClient() as client:
        # Build detailed function signatures from OpenAPI spec
        functions_detail = []

        # Parse the OpenAPI spec to extract function signatures
        if "paths" in spec_data:
            for path, methods in spec_data["paths"].items():
                for method, operation in methods.items():
                    if method.lower() not in [
                        "get",
                        "post",
                        "put",
                        "delete",
                        "patch",
                        "options",
                        "head",
                    ]:
                        continue

                    operation_id = operation.get("operationId")
                    if not operation_id:
                        continue

                    params = []

                    # Extract parameters
                    if "parameters" in operation:
                        for param in operation["parameters"]:
                            param_name = param.get("name", "unknown")
                            param_required = param.get("required", False)

                            if param_required:
                                params.append(f"{param_name}")
                            else:
                                params.append(f"{param_name}=None")

                    # Check for request body
                    if "requestBody" in operation:
                        params.append("body=" + json.dumps(operation["requestBody"]))

                    params_str = ", ".join(params) if params else ""
                    functions_detail.append(f"{operation_id}({params_str})")

        # Fallback: just list function names
        if not functions_detail:
            for func_name in client.functions.keys():
                functions_detail.append(f"{func_name}(**kwargs)")

        functions_text = "\n".join(functions_detail)
        spec = f"\n\nAvailable functions:\n{functions_text}"

    return TextContent(text=spec)


@pipe_func()
async def obtain_openapi_model(working_memory: WorkingMemory) -> OpenAPISpec:
    """
    Fetch and parse OpenAPI specification into a structured Pydantic model.

    Returns:
        OpenAPISpec: Structured representation of the OpenAPI specification
    """
    openapi_url = working_memory.get_stuff_as_text("openapi_url").text.strip()
    response = requests.get(url=openapi_url)
    spec_data = response.json()

    # Parse the raw JSON into our Pydantic model
    # The model will validate and structure the data
    openapi_spec = OpenAPISpec(**spec_data)

    return openapi_spec


@pipe_func()
async def extract_available_functions(
    working_memory: WorkingMemory,
) -> ListContent[FunctionInfo]:
    """
    Extract available functions from OpenAPI spec as a list of FunctionInfo objects.

    Returns:
        ListContent: List of FunctionInfo objects with function_name and description
    """
    openapi_url = working_memory.get_stuff_as_text("openapi_url").text.strip()
    response = requests.get(url=openapi_url)
    spec_data = response.json()

    functions: List[FunctionInfo] = []

    # Parse the OpenAPI spec to extract function names and descriptions
    if "paths" in spec_data:
        for path, methods in spec_data["paths"].items():
            for method, operation in methods.items():
                if method.lower() not in [
                    "get",
                    "post",
                    "put",
                    "delete",
                    "patch",
                    "options",
                    "head",
                ]:
                    continue

                operation_id = operation.get("operationId")
                if not operation_id:
                    continue

                # Get description from summary or description field
                description = operation.get("summary") or operation.get("description")

                functions.append(FunctionInfo(function_name=operation_id, description=description))

    # Convert to ListContent with FunctionInfo items
    return ListContent(items=functions)


@pipe_func()
async def get_function_details(working_memory: WorkingMemory) -> FunctionDetails:
    """
    Get detailed information about a specific function from the OpenAPI spec.
    This includes HTTP method, path, parameters, and request body schema.

    Returns:
        FunctionDetails: Complete details needed to make the API request
    """
    # Get the structured OpenAPISpec from working memory
    openapi_spec = working_memory.get_stuff_as("openapi_spec", OpenAPISpec)
    function_choice = working_memory.get_stuff_as("function_choice", FunctionChoice)
    function_name = function_choice.function_name

    # Search for the function in the OpenAPI spec
    for path, path_item in openapi_spec.paths.items():
        # Check each HTTP method
        for method_name in ["get", "post", "put", "delete", "patch", "options", "head"]:
            operation = getattr(path_item, method_name, None)

            if operation and operation.operationId == function_name:
                # Found the function! Extract all details
                parameters: List[ParameterDetail] = []

                # Extract parameters from the structured model
                if operation.parameters:
                    for param in operation.parameters:
                        param_type = None
                        param_default = None
                        if param.schema_:
                            param_type = param.schema_.get("type")
                            param_default = param.schema_.get("default")

                        parameters.append(
                            ParameterDetail(
                                name=param.name,
                                param_in=param.in_,
                                required=param.required or False,
                                param_type=param_type,
                                description=param.description,
                                default=param_default,
                            )
                        )

                # Extract request body information
                request_body_required = False
                request_body_schema = None
                if operation.requestBody:
                    request_body_required = operation.requestBody.required or False
                    request_body_schema = operation.requestBody.content

                # Get description (prefer summary over description)
                description = operation.summary or operation.description

                # Get tags
                tags = operation.tags

                return FunctionDetails(
                    function_name=function_name,
                    http_method=method_name.upper(),
                    path=path,
                    description=description,
                    parameters=parameters,
                    request_body_required=request_body_required,
                    request_body_schema=request_body_schema,
                    tags=tags,
                )

    # Function not found
    raise ValueError(f"Function '{function_name}' not found in OpenAPI specification")
