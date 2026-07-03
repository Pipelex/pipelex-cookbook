from pipelex.cogt.inference.inference_worker_abstract import InferenceWorkerAbstract
from pipelex.cogt.model_backends.backend import InferenceBackend
from pipelex.cogt.model_backends.model_spec import InferenceModelSpec
from pipelex.plugins.contract import PLUGIN_API_VERSION
from pipelex.plugins.inference_backend_registry import InferenceFamily
from pipelex.plugins.registrar import PluginRegistrar
from pipelex.plugins.sdk_client_registry import SdkClientRegistry
from pipelex.reporting.reporting_protocol import ReportingProtocol


def _make_hello_llm_worker(
    *,
    inference_model: InferenceModelSpec,
    backend: InferenceBackend,
    sdk_clients: SdkClientRegistry,
    reporting_delegate: ReportingProtocol | None,
) -> InferenceWorkerAbstract:
    # Heavy work belongs here, inside the closure — not at module import time.
    # A real plugin would `require_sdk(...)` then build/memoize its SDK client via
    # `sdk_clients.get_or_create(...)`; the hello worker needs neither.
    from hello_inference_plugin.hello_llm_worker import HelloLLMWorker

    return HelloLLMWorker(inference_model=inference_model, reporting_delegate=reporting_delegate)


async def _list_hello_models(
    *,
    sdk: str,
    backend_name: str,
    backend: InferenceBackend,
    flat: bool,
    any_listed: bool,
) -> None:
    from hello_inference_plugin.hello_list import list_hello_models

    list_hello_models(sdk=sdk, backend_name=backend_name, backend=backend, flat=flat, any_listed=any_listed)


class HelloInferencePlugin:
    """Example out-of-tree inference-backend plugin: serves the `hello` SDK token.

    `register` is the only method Pipelex calls, and it must stay side-effect-free:
    menu calls on the registrar only — no I/O, no client construction.
    """

    name = "hello_inference"
    targets_api = PLUGIN_API_VERSION

    def register(self, registrar: PluginRegistrar) -> None:
        registrar.add_inference_backend(family=InferenceFamily.LLM, sdk="hello", make_worker=_make_hello_llm_worker)
        # Optional companion seam: powers `pipelex show models` for this backend.
        registrar.add_model_lister(sdk="hello", lister=_list_hello_models)
