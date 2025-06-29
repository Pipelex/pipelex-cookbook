import asyncio
import json
import os
from typing import Any, Dict, List, Optional, Type

import httpx
from pipelex import pretty_print
from pipelex.cogt.llm.llm_job import LLMJob
from pipelex.cogt.llm.llm_job_components import LLMJobParams
from pipelex.cogt.llm.llm_job_factory import LLMJobFactory
from pipelex.cogt.llm.llm_models.llm_engine import LLMEngine
from pipelex.cogt.llm.llm_models.llm_family import LLMFamily
from pipelex.cogt.llm.llm_models.llm_model import LATEST_VERSION_NAME, LLMModel
from pipelex.cogt.llm.llm_models.llm_platform import LLMPlatform
from pipelex.cogt.llm.llm_worker_abstract import LLMWorkerAbstract
from pipelex.cogt.llm.llm_worker_factory import LLMWorkerFactory
from pipelex.cogt.llm.token_category import NbTokensByCategoryDict, TokenCategory
from pipelex.hub import get_plugin_manager, get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.reporting.reporting_protocol import ReportingProtocol
from pipelex.tools.typing.pydantic_utils import BaseModelTypeVar
from typing_extensions import override

from tests.integration.pipelex.cogt.test_data import LLMTestConstants, Person

EXTERNAL_LLM_NAME = "openai_external_llm"


class ExternalLLMWorkerOpenAI(LLMWorkerAbstract):
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
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.base_url = "https://api.openai.com/v1"
        self.model = "gpt-4o"

    @property
    @override
    def desc(self) -> str:
        return "LLM Worker using OpenAI REST API"

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

    async def _make_openai_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to OpenAI API"""
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            json_response = response.json()
            if not isinstance(json_response, dict):
                raise ValueError(f"Invalid response from OpenAI: {json_response}")
            dict_response: Dict[str, Any] = json_response
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

        response_data = await self._make_openai_request(payload)

        # Update token usage
        self._update_token_usage(llm_job, response_data)

        # Extract response content
        choices = response_data.get("choices", [])
        if not choices:
            raise ValueError("No choices in OpenAI response")

        content = choices[0]["message"]["content"]
        if not content:
            raise ValueError("No content in OpenAI response")
        if not isinstance(content, str):
            raise ValueError(f"Invalid content in OpenAI response: {content}")
        return content

    @override
    async def _gen_object(
        self,
        llm_job: LLMJob,
        schema: Type[BaseModelTypeVar],
    ) -> BaseModelTypeVar:
        messages = self._make_messages(llm_job)

        # Add instruction for JSON output
        schema_instruction = f"Respond with a valid JSON object that matches this schema: {schema.model_json_schema()}"

        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += f"\n\n{schema_instruction}"
        else:
            messages.append({"role": "user", "content": schema_instruction})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": llm_job.job_params.temperature or 0.7,
            "response_format": {"type": "json_object"},
        }

        if llm_job.job_params.max_tokens:
            payload["max_tokens"] = llm_job.job_params.max_tokens

        if llm_job.job_params.seed:
            payload["seed"] = llm_job.job_params.seed

        response_data = await self._make_openai_request(payload)

        # Update token usage
        self._update_token_usage(llm_job, response_data)

        # Extract and parse JSON response
        choices = response_data.get("choices", [])
        if not choices:
            raise ValueError("No choices in OpenAI response")

        content = choices[0]["message"]["content"]
        if not content:
            raise ValueError("No content in OpenAI response")

        try:
            json_data = json.loads(content)
            return schema(**json_data)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            raise ValueError(f"Failed to parse JSON response: {e}") from e


async def gen_text_and_object_using_external_plugin(plugin_name: str):
    llm_worker = LLMWorkerFactory.make_llm_worker_from_external_plugin(
        external_plugin_name=plugin_name,
        reporting_delegate=get_report_delegate(),
    )
    llm_job = LLMJobFactory.make_llm_job_from_prompt_contents(
        system_text=None,
        user_text=LLMTestConstants.USER_TEXT_SHORT,
        llm_job_params=LLMJobParams(
            temperature=0.5,
            max_tokens=None,
            seed=None,
        ),
    )
    generated_text = await llm_worker.gen_text(llm_job=llm_job)
    assert generated_text
    pretty_print(generated_text)
    generated_object = await llm_worker.gen_object(llm_job=llm_job, schema=Person)
    assert generated_object
    pretty_print(generated_object)


# start Pipelex
Pipelex.make()
# register external plugin
get_plugin_manager().register_plugin(name=EXTERNAL_LLM_NAME, plugin_class=ExternalLLMWorkerOpenAI)
# run sample using asyncio
asyncio.run(gen_text_and_object_using_external_plugin(plugin_name=EXTERNAL_LLM_NAME))
