# General rules

## Repo structure

The purpose of pipelex-cookbook is to showcase samples based on the library named `pipelex`.
This python 3.11 repo named pipelex-cookbook has several packages placed at the root of the repo.

- `core` -> official samples
- `community` -> placeholder, we don't have community samples yet
- `utils` -> utilities and helpers
- `pipelex_libraries` -> pipelines defined using the Pipelex language (.toml and .py files)
- `tests`

## Code Style & formatting

- Imitate existing style
- Use type hints
- Respect Pydantic v2 standard
- Use Typer for CLIs
- Use explicit keyword arguments for function calls with multiple parameters (e.g., `func(arg_name=value)` not just `func(value)`)
- Add trailing commas to multi-line lists, dicts, function arguments, and tuples with >2 items (helps with cleaner diffs and prevents syntax errors when adding items)
- All imports inside this repo's packages must be absolute package paths from the root

## Writing tests

- Always use pytest

### Test file structure

- Name test files with `test_` prefix
- Use descriptive names that match the functionality being tested
- Place test files in the appropriate subdirectory of `tests/`:
- More precisely place async tests inside the `asynch` subdirectory

### Markers

Apply the appropriate markers:
- "llm: uses an LLM to generate text or objects"
- "imgg: uses an image generation AI"
- "inference: uses either an LLM or an image generation AI"
- "gha_disabled: will not be able to run properly on GitHub Actions"
- "codex_disabled: will not be able to run properly on Codex"  # typically relevant for tests that need internet access, which Codex doesn't allow

Several markers may be applied. For instance, if the test uses an LLM, then it uses inference, so you must mark with both `inference`and `llm`.

### Test Class Structure

Always group the tests of a module into a test class:

```python
@pytest.mark.llm
@pytest.mark.inference
@pytest.mark.asyncio(loop_scope="class")
class TestFooBar:
    @pytest.mark.parametrize(
        "topic test_case_blueprint",
        [
            TestCases.CASE_1,
            TestCases.CASE_2,
        ],
    )
    async def test_pipe_processing(
        self,
        request: FixtureRequest,
        topic: str,
        test_case_blueprint: StuffBlueprint,
    ):
        # Test implementation
```

Sometimes it can be convenient to access the test's name in its body, for instance to include into a job_id. To achieve that, add the argument `request: FixtureRequest` into the signature and then you can get the test name using `cast(str, request.node.originalname),  # type: ignore`. 

## Linting & checking

- Run `make lint` -> it runs `ruff check . --fix` to enforce all our linting rules
- Run `make pyright` -> it typechecks with pyright using proper settings
- Run `make mypy` -> it typechecks with mypy using proper settings
    - if you added a dependency and mypy complains that it's not typed, add it to the list of modules in [[tool.mypy.overrides]] in pyproject.toml, be sure to signal it in your PR recap so that maintainers can look for existing stubs

## Testing

- Always test with `make codex-tests` -> it runs pytest on our `tests/` directory using proper settings
- If all unit tests pass, run `make validate` -> it runs a minimal version of our app with just the inits and data loading

## PR Instructions

- Run `make fix-unused-imports` -> removes unused imports, required to validate PR
- Re-run checks in one call with `make check` -> formatting and linting with Ruff, type-checking with Pyright and Mypy
- Re-run `make codex-tests`
- Write a one-line summary of the changes.
- Be sure to list changes made to configs, tests and dependencies
