import asyncio
import json
from typing import Any, Dict, List, Optional, Type, cast

import httpx
from pipelex.cogt.exceptions import LLMCompletionError
from pipelex.cogt.llm.llm_job import LLMJob
from pipelex.cogt.llm.llm_worker_abstract import LLMWorkerAbstract
from pipelex.cogt.usage.token_category import NbTokensByCategoryDict, TokenCategory
from pipelex.reporting.reporting_protocol import ReportingProtocol
from pipelex.tools.environment import get_required_env
from pipelex.tools.exceptions import CredentialsError
from pipelex.tools.typing.pydantic_utils import BaseModelTypeVar, format_pydantic_validation_error
from pydantic import ValidationError
from typing_extensions import override


class LLMPluginExampleUsingOpenAI(LLMWorkerAbstract):
    """
    OpenAI External LLM Worker that implements the OpenAI chat completion REST API
    using direct HTTP calls (not the OpenAI SDK).

    Requires OPENAI_API_KEY environment variable to be set.
    """

    def __init__(
        self,
        reporting_delegate: Optional[ReportingProtocol] = None,
    ):
        LLMWorkerAbstract.__init__(self, reporting_delegate=reporting_delegate)
        self.api_key = get_required_env("OPENAI_API_KEY")
        if not self.api_key:
            raise CredentialsError("OPENAI_API_KEY environment variable is required")
        self.base_url = "https://api.openai.com/v1"
        self.model = "gpt-4o"
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client with proper lifecycle management."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    @override
    def teardown(self) -> None:
        """Clean up resources when the worker is no longer needed.

        This should be called by external code when the worker instance
        is no longer needed to properly close HTTP connections and free resources.
        """
        if self._client is not None and not self._client.is_closed:
            asyncio.create_task(self._client.aclose())
            self._client = None

    @property
    @override
    def desc(self) -> str:
        return "LLM Worker using OpenAI REST API"

    @property
    @override
    def is_gen_object_supported(self) -> bool:
        return True

    def _make_messages(self, llm_job: LLMJob) -> List[Dict[str, str]]:
        """Build OpenAI messages format from LLMJob"""
        messages: List[Dict[str, str]] = []
        if llm_job.llm_prompt.system_text:
            messages.append({"role": "system", "content": llm_job.llm_prompt.system_text})
        if llm_job.llm_prompt.user_text:
            messages.append({"role": "user", "content": llm_job.llm_prompt.user_text})
        if llm_job.llm_prompt.user_images:
            raise NotImplementedError("Images are not supported in this example")
        return messages

    async def _make_http_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to OpenAI API"""
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

        client = await self._get_client()
        response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        json_response = response.json()
        if not isinstance(json_response, dict):
            raise LLMCompletionError(f"Invalid response from OpenAI: {json_response}")
        dict_response: Dict[str, Any] = cast(Dict[str, Any], json_response)
        return dict_response

    def _update_token_usage(self, llm_job: LLMJob, response_data: Dict[str, Any]) -> None:
        """Update token usage from OpenAI response"""
        if llm_tokens_usage := llm_job.job_report.llm_tokens_usage:
            usage = response_data.get("usage", {})
            nb_tokens_by_category: NbTokensByCategoryDict = {
                TokenCategory.INPUT: usage.get("prompt_tokens", 0),
                TokenCategory.OUTPUT: usage.get("completion_tokens", 0),
            }
            llm_tokens_usage.nb_tokens_by_category = nb_tokens_by_category

    @override
    async def _gen_text(
        self,
        llm_job: LLMJob,
    ) -> str:
        messages = self._make_messages(llm_job)

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": llm_job.job_params.temperature or 0.7,
        }

        if llm_job.job_params.max_tokens:
            payload["max_tokens"] = llm_job.job_params.max_tokens

        if llm_job.job_params.seed:
            payload["seed"] = llm_job.job_params.seed

        response_data = await self._make_http_request(payload)

        # Update token usage
        self._update_token_usage(llm_job, response_data)

        # Extract response content
        choices = response_data.get("choices", [])
        if not choices:
            raise LLMCompletionError("No choices in OpenAI response")

        content = choices[0]["message"]["content"]
        if not content:
            raise LLMCompletionError("No content in OpenAI response")
        if not isinstance(content, str):
            raise LLMCompletionError(f"Invalid content in OpenAI response: {content}")
        return content

    @override
    async def _gen_object(
        self,
        llm_job: LLMJob,
        schema: Type[BaseModelTypeVar],
    ) -> BaseModelTypeVar:
        messages = self._make_messages(llm_job)

        # Get the JSON schema for structured output
        json_schema = schema.model_json_schema()

        # Use OpenAI's structured outputs with the actual schema
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": llm_job.job_params.temperature or 0.5,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": f"{schema.__name__.lower()}_schema", "schema": json_schema},
            },
        }

        if llm_job.job_params.max_tokens:
            payload["max_tokens"] = llm_job.job_params.max_tokens

        if llm_job.job_params.seed:
            payload["seed"] = llm_job.job_params.seed

        response_data = await self._make_http_request(payload)

        # Update token usage
        self._update_token_usage(llm_job, response_data)

        # Extract and parse JSON response
        choices = response_data.get("choices", [])
        if not choices:
            raise LLMCompletionError("No choices in completion response")

        content = choices[0]["message"]["content"]
        if not content:
            raise LLMCompletionError("No content in completion response")

        try:
            json_data = json.loads(content)
            return schema.model_validate(json_data)
        except json.JSONDecodeError as exc:
            raise LLMCompletionError(f"Failed to parse JSON response from completion: {exc}") from exc
        except ValidationError as exc:
            error_msg = format_pydantic_validation_error(exc)
            raise LLMCompletionError(f"Failed to validate JSON response from completion: {error_msg}") from exc
