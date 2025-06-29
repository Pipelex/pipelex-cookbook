import asyncio
from typing import Type

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
from pipelex.tools.typing.pydantic_utils import BaseModelTypeVar
from polyfactory.factories.pydantic_factory import ModelFactory
from typing_extensions import override

from tests.integration.pipelex.cogt.test_data import LLMTestConstants, Person

EXTERNAL_LLM_NAME = "mock_external_llm"


class MockExternalLLMWorker(LLMWorkerAbstract):
    @override
    async def _gen_text(
        self,
        llm_job: LLMJob,
    ) -> str:
        response_text = f"This is a mock LLM response from '{self.__class__}'"

        if llm_tokens_usage := llm_job.job_report.llm_tokens_usage:
            nb_tokens_by_category: NbTokensByCategoryDict = {
                TokenCategory.INPUT: 100,
                TokenCategory.OUTPUT: 100,
            }
            llm_tokens_usage.nb_tokens_by_category = nb_tokens_by_category
        return response_text

    @override
    async def _gen_object(
        self,
        llm_job: LLMJob,
        schema: Type[BaseModelTypeVar],
    ) -> BaseModelTypeVar:
        class ObjectFactory(ModelFactory[schema]):  # type: ignore
            __model__ = schema
            __use_examples__ = True

        obj = ObjectFactory.build()
        return obj


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
get_plugin_manager().register_plugin(name=EXTERNAL_LLM_NAME, plugin_class=MockExternalLLMWorker)
# run sample using asyncio
asyncio.run(gen_text_and_object_using_external_plugin(plugin_name=EXTERNAL_LLM_NAME))
