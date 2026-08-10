# Using Inference Plugins

This example shows how Pipelex discovers **inference-backend plugins**: installable Python packages that teach Pipelex how to serve models for a given `sdk` token. The `hello-inference-plugin/` package in this directory is a complete, minimal plugin — a deterministic "LLM" that always answers with the same haiku, so it runs anywhere with **no API key and no network**.

## What's in here

- `hello_plugin.mthds` — a one-pipe method whose model handle `hello-1` resolves to the plugin's backend.
- `hello_inference_plugin/` — the plugin package:
  - `pyproject.toml` declares the `pipelex.plugins.kernel` entry point. That single line is the whole integration: once the package is installed, Pipelex discovers the plugin automatically — presence is the source of truth, there is no enable-list.
  - `hello_inference_plugin/hello_plugin.py` — the `HelloInferencePlugin` class (`name`, `targets_api`, and a side-effect-free `register` that contributes an inference backend for `(family="llm", sdk="hello")` plus an optional model lister).
  - `hello_inference_plugin/hello_llm_worker.py` — the worker: subclasses `LLMWorkerAbstract` and implements `_gen_text` deterministically.
  - `hello_inference_plugin/hello_list.py` — the optional lister behind `pipelex show models hello`.

The model-side wiring lives in the cookbook's `.pipelex/inference/` config:

- `backends.toml` declares the `[hello]` backend (enabled, no key).
- `backends/hello.toml` declares model `hello-1` with `sdk = "hello"` — the token that selects the plugin's worker factory.
- `routing_profiles.toml` routes `hello-1` to the `hello` backend via an `optional_routes` entry (inert if you disable the backend).

## Run it

Install the plugin package (this is the step being demonstrated):

```bash
uv pip install -e examples/c_advanced/using_inference_plugins/hello_inference_plugin
```

Check that Pipelex discovered it:

```bash
pipelex plugins list        # hello_inference | external | registered
pipelex show models hello   # lists hello-1
```

Run the method — no credentials needed:

```bash
pipelex run bundle examples/c_advanced/using_inference_plugins/hello_plugin.mthds
```

You get the plugin's deterministic haiku as the pipe output.

## See the failure mode

Uninstall the package and run again:

```bash
uv pip uninstall hello-inference-plugin
pipelex run bundle examples/c_advanced/using_inference_plugins/hello_plugin.mthds
```

Pipelex fails loud at worker-creation time: `No inference backend registered for sdk 'hello' in the llm family. Is its plugin installed and enabled?` — the config still resolves; only the worker factory is missing.

## Going further

To wrap a real SDK (client construction, `require_sdk` dependency guards, client memoization via `SdkClientRegistry`), see the Pipelex docs: [Inference Backend Plugins](https://docs.pipelex.com/latest/under-the-hood/inference-backend-plugins/).
