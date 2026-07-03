from pipelex.cogt.exceptions import LLMCapabilityError
from pipelex.cogt.llm.llm_job import LLMJob
from pipelex.cogt.llm.llm_worker_abstract import LLMWorkerAbstract
from pipelex.cogt.usage.token_category import TokenCategory
from pipelex.tools.typing.pydantic_utils import BaseModelTypeVar
from typing_extensions import override

# The whole point of this worker is to be deterministic and require no credentials:
# every completion is the same haiku, so the example runs anywhere, offline, for free.
HELLO_HAIKU = """Hello, World! I am
a plugin-served model — no
keys, no clouds, just code."""


class HelloLLMWorker(LLMWorkerAbstract):
    """Deterministic, zero-key LLM worker: always completes with the same haiku.

    The base class owns the whole job lifecycle (validation, capability checks
    from the model spec, usage reporting, telemetry) — a worker only implements
    the actual generation. A real plugin would hold an SDK client and call a
    remote model here; see the Pipelex docs page on inference-backend plugins
    for a walkthrough that wraps an actual SDK.
    """

    @override
    async def _gen_text(self, llm_job: LLMJob) -> str:
        completion_text = HELLO_HAIKU
        if llm_tokens_usage := llm_job.job_report.llm_tokens_usage:
            prompt_text = llm_job.llm_prompt.user_text or ""
            llm_tokens_usage.nb_tokens_by_category = {
                TokenCategory.INPUT: len(prompt_text.split()),
                TokenCategory.OUTPUT: len(completion_text.split()),
            }
        return completion_text

    @override
    async def _gen_object(
        self,
        llm_job: LLMJob,
        *,
        schema: type[BaseModelTypeVar],
    ) -> BaseModelTypeVar:
        # Never reached in practice: the model spec declares outputs = ["text"] only,
        # so `is_gen_object_supported` is False and pipes won't route structured
        # generation here. Raising keeps the worker honest if called directly.
        msg = f"Model '{self.inference_model.name}' does not support structured output — it only echoes a haiku."
        raise LLMCapabilityError(msg)
