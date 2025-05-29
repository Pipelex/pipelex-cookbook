# General rules

## Repo structure

The purpose of pipelex-cookbook is to showcase samples based on the library named `pipelex`.
This python 3.11 repo named pipelex-cookbook has several packages placed at the root of the repo.

- `core` -> official samples
- `community` -> placeholder, we don't have community samples yet
- `utils` -> utilities and helpers
- `pipelex_libraries` -> pipelines defined using the Pipelex language (.tomland .py files)
- `tests`

## Code Style & formatting

- Imitate existing style
- After editing code, run `make format` -> it runs `ruff format .` with proper settings
- All imports inside this repo's packages must be absolute package paths from the root

## Linting & checking

- Run `make lint` -> it runs `ruff check . --fix` to enforce all our linting rules
- Run `make pyright` -> it typechecks with pyright using proper settings
- Run `make mypy` -> it typechecks with mypy using proper settings
    - if you added a dependency and mypy complains that it's not typed, add it to the list of modules in [[tool.mypy.overrides]] in pyproject.toml, be sure to signal it in your PR recap so that maintainers can look for existing stubs

## Testing

- Always test with `make runtests` -> it runs pytest on our `tests/` directory using proper sttings
- If all unit tests pass, run `make run-setup` -> it runs a minimal version of our app with just the inits and data loading

## PR Instructions

- One-line summary of the change.
- Be sure to list changes made to configs, tests and dependencies
