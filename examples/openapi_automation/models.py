from typing import Any, Dict, List, Optional

from pipelex.core.stuffs.structured_content import StructuredContent
from pydantic import BaseModel, Field


class FunctionParameter(StructuredContent):
    name: str = Field(description="parameter name")
    value: str = Field(description="parameter value")
    type: str = Field(description="parameter type")


# OpenAPI Specification Models
class OpenAPIParameter(BaseModel):
    name: str
    in_: str = Field(alias="in")
    required: Optional[bool] = False
    description: Optional[str] = None
    schema_: Optional[Dict[str, Any]] = Field(default=None, alias="schema")


class OpenAPIRequestBody(BaseModel):
    description: Optional[str] = None
    required: Optional[bool] = False
    content: Optional[Dict[str, Any]] = None


class OpenAPIResponse(BaseModel):
    description: Optional[str] = None
    content: Optional[Dict[str, Any]] = None


class OpenAPIOperation(BaseModel):
    operationId: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[List[OpenAPIParameter]] = None
    requestBody: Optional[OpenAPIRequestBody] = None
    responses: Optional[Dict[str, OpenAPIResponse]] = None
    tags: Optional[List[str]] = None


class OpenAPIPathItem(BaseModel):
    get: Optional[OpenAPIOperation] = None
    post: Optional[OpenAPIOperation] = None
    put: Optional[OpenAPIOperation] = None
    delete: Optional[OpenAPIOperation] = None
    patch: Optional[OpenAPIOperation] = None
    options: Optional[OpenAPIOperation] = None
    head: Optional[OpenAPIOperation] = None


class OpenAPIInfo(BaseModel):
    title: str
    version: str
    description: Optional[str] = None


class OpenAPISpec(StructuredContent):
    openapi: str = Field(description="OpenAPI version")
    info: OpenAPIInfo = Field(description="API metadata")
    paths: Dict[str, OpenAPIPathItem] = Field(description="API endpoints")
    components: Optional[Dict[str, Any]] = Field(default=None, description="Reusable components")
    servers: Optional[List[Dict[str, Any]]] = Field(default=None, description="API servers")


class FunctionInfo(StructuredContent):
    function_name: str = Field(description="The operation ID / function name")
    description: Optional[str] = Field(default=None, description="Function description")


class FunctionChoice(StructuredContent):
    explanation: str = Field(description="Explanation of the choice.")
    function_name: str = Field(description="Name of the function.")


class ParameterDetail(StructuredContent):
    """Detailed parameter information for API calls"""

    name: str = Field(description="Parameter name")
    param_in: str = Field(description="Where the parameter goes: path, query, header, cookie")
    required: bool = Field(default=False, description="Whether the parameter is required")
    param_type: Optional[str] = Field(default=None, description="Parameter data type")
    description: Optional[str] = Field(default=None, description="Parameter description")
    default: Optional[Any] = Field(default=None, description="Default value if any")


class FunctionDetails(StructuredContent):
    """Complete details needed to make an API request"""

    function_name: str = Field(description="The operation ID / function name")
    http_method: str = Field(description="HTTP method (GET, POST, PUT, DELETE, etc.)")
    path: str = Field(description="API endpoint path")
    description: Optional[str] = Field(default=None, description="Operation description")
    parameters: List[ParameterDetail] = Field(default_factory=list, description="List of parameters")
    request_body_required: bool = Field(default=False, description="Whether a request body is required")
    request_body_schema: Optional[Dict[str, Any]] = Field(default=None, description="Request body schema if applicable")
    tags: Optional[List[str]] = Field(default=None, description="Operation tags")


class RequestDetails(StructuredContent):
    """Holds the actual parameter values needed to make an API request"""

    function_name: str = Field(description="The operation ID / function name")
    http_method: str = Field(description="HTTP method (GET, POST, PUT, DELETE, etc.)")
    path: str = Field(description="API endpoint path")
    query_parameters: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters and their values")
    path_parameters: Optional[Dict[str, Any]] = Field(default=None, description="Path parameters and their values")
    header_parameters: Optional[Dict[str, Any]] = Field(default=None, description="Header parameters and their values")
    cookie_parameters: Optional[Dict[str, Any]] = Field(default=None, description="Cookie parameters and their values")
    request_body: Optional[Dict[str, Any]] = Field(default=None, description="Request body data if applicable")
