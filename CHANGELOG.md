# Changelog

## [v0.1.13] - 2025-06-09

- Adapt to the new pipe input handling in Pipelex v0.3.0

## [v0.1.12] - 2025-06-06

- Bumped pipelex to v0.2.14: generalized the new `execute_pipeline` method, enabling to track pipelines from beginning to end with inference cost reporting

## [v0.1.11] - 2025-06-04

### Added

**2 samples for power extraction**:

- `extract_dpe`: Extract structured data from French "Diagnostics de Performance Energétique". It illustrates how Pipelex can enable you to tackle strongly formatted PDF extraction by combining OCR models, LLM vision, and validation.
- `extract_proof_of_purchase`: Extract structured data from proofs of purchase. Another use case for extracting structured data from unstructured documents.

## [v0.1.9] - 2025-06-03

- Compatible with python-version: `["3.10", "3.11", "3.12", "3.13"]`
- Use `pretty-sugar`
- Sample Pipeline to improve a tweet
- Various fixes and improvements in docs and code
- Use renamed `Mission` to `Pipeline`
- `Makefile`: avoid defaulting `pytest` to verbose. Setup target `make test-xdist` = Run unit tests with xdist, make it the default for shorthand `make t`. The old `make t` is now `make tp` (test-with-prints)

## [v0.1.8] - 2025-05-30

### Added

**Codex support**
* **AGENTS.md**: contributor guide for agends such as OpenAI's Codex, covering repo layout, code style, testing, linting and PR workflow
* New pytest marker `codex_disabled` to disable tests that can't run on Codex, because they require internet access for instance

* Unit tests in `tests/test_results_utils.py`
* New GitHub Action **changelog-check.yml** to verify that every release branch includes a matching changelog entry
* Pipeline **pipe.extract\_page\_contents\_and\_views\_from\_pdf** plus updated TOML definitions
* Makefile targets: `validate`, `codex-tests`, `gha-tests`, `test-ocr`, `test-imgg` and shorthand aliases
* Examples refactored into callable async functions so they can be imported and exercised by tests (yet to be added)

### Changed

* **uv** handling: `pyproject.toml`, requires `uv >=0.7.2`; `check-uv` installs or upgrades to the minimum compatible version
* Large Makefile refactor
  * Replaced hard-coded paths with `VENV_*` macros
  * Legacy `runtests` split into `codex-tests` and `gha-tests`
* Examples cleaned up: added type hints, used cost reports, exported results via `utils.results_utils`

### Deprecated

* `make runtests` superseded by `make codex-tests` and `make gha-tests`

### Internal

* Added `.cursor` and `.git` workflow files to Ruff exclude list

## [v0.1.7] - 2025-05-26

### Added:
- New file `pipelex_libraries/llm_integrations/custom.toml` introducing first-class support for custom LLMs:  
  - **Gemma 3 4B** (`custom-gemma-3."gemma3:4b".latest`)  
  - **Llama 4 Scout** (`custom-llama-4."llama4:scout".latest`)  

### Changed:
- Core dependency **pipelex** upgraded from `0.2.4` to `0.2.7`.
- Dependency **kajson** upgraded from `0.1.0` to `0.1.4`.

### Fixed:
- Incorrect version constraint on `pipelex` in `pyproject.toml`.

## [v0.1.6] - 2025-05-25

- Fix version dependency to Pipelex

## [v0.1.5] - 2025-05-25

- Reorganize repo
- Replace license ELv2 by MIT and remove Reuse dependency

## [v0.1.3] - 2025-05-22

- Samples for OCR:
    - pdf_1_simple_ocr.py: use Mistram OCR to extract text from image or pdf
    - pdf_2_power_extractor.py: use OCR in combination with a VLM (Vision Language Model) to catch all the details and reach higher reliability

- WIP Sample for the new execute_mission API: it tracks costs related to a specific mission_id

- Fix for Windows: load text files using explicit "utf-8" encoding

## [v0.1.1] - 2025-05-19

- Polish pyproject metadata

## [v0.1.0] - 2025-05-13

- Initial release 🎉
