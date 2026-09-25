# Adding a recipe

A recipe shows one way of using a method in depth, on a real case, with code the cookbook's checks hold to the method it calls. [README.md](README.md) explains the parts; this is the order to add a Python code recipe in.

## 1. Choose the method and pin it

Pick a cookbook method or a method from the [method library](https://github.com/Pipelex/methods), and write its address pinned to a release tag: `github.com/Pipelex/pipelex-cookbook/<name>@vX.Y.Z` or `github.com/Pipelex/methods/<name>@vX.Y.Z`. A recipe never calls an address without a tag, since it would float with the default branch while the recipe's types stay put.

## 2. Write the sidecar and generate the types

Create `recipes/code/python/<recipe>/generated/<method>/sources.json`, the one file of the tree you write by hand:

```json
{
  "comment": "The address and the codegen target these types were generated from. In the cookbook, `make refresh` regenerates the tree from this file, and `make check-codegen` checks it against codegen.lock; never edit a generated file by hand.",
  "generator": "pipelex-cookbook",
  "method": { "method_ref": "github.com/Pipelex/methods/<name>@vX.Y.Z" },
  "target": "python-pydantic"
}
```

Then run `make refresh` with `PIPELEX_API_KEY` set. It writes `models.py`, `codegen.lock` and the two `__init__.py` files that make the tree importable. Commit them as they are.

## 3. Write the script

One script, `<recipe>/<name>.py`, that a reader runs with `uv run <name>.py`:

- It opens with its inline dependencies, naming `pipelex-sdk` pinned exactly, and anything else it imports directly:

  ```python
  # /// script
  # requires-python = ">=3.11"
  # dependencies = ["pipelex-sdk==0.12.0", "httpx>=0.24", "pydantic>=2.10.6"]
  # ///
  ```

  The SDK brings `httpx`, `pydantic` and `mthds` with it, but a script that imports one of them declares it too, so it keeps working when the SDK's own dependencies move. `PipelineRequestError`, the base of every request error, is imported from `mthds.protocol.exceptions`.

- Its docstring says what it does, how to run it, and that `PIPELEX_API_KEY` must be set and each run spends credit.
- It holds the pinned address in a `METHOD_REF` constant, calls `PipelexAPIClient().start_and_wait(method_ref=METHOD_REF, inputs=…)`, and reads `results.main_stuff` through the generated models: `Model.model_validate(...)` for a single output, and for a list output a `TypeAdapter` that reads both a bare list and the `{"items": [...]}` envelope, as `code/python/csv-batch/batch.py` does.
- It prints its progress to stderr and its result to stdout or to a file, and leaves the typed errors of `pipelex_sdk.errors` to propagate unless the recipe is about handling them.

## 4. Write the README

`README.md` in the recipe's directory, in the order the other recipes follow: what the recipe shows and why it matters, what it needs (as links), how to run it, what you get, and how it is built. It explains its door on its case and links to the docs for the rest.

## 5. Prove it and check it

- Run it once on production, as a reader would, and read the result against what the README promises.
- Run `make agent-check`, which includes `check-recipes` and `check-codegen`, then `make check-recipe-types`, which type-checks the script in its own environment, and `make check-hosted`, which validates the pinned address on production and checks that the types come from what it resolves to.
- Add the recipe to `recipes/README.md`.
