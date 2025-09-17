# Changelog

## [v0.5.1] - 2025-09-17

- Cleanup env example

## [v0.5.0] - 2025-09-17

- Bump `pipelex` to `v0.10.1`: See `Pipelex` changelog [here](https://docs.pipelex.com/changelog/)

## [v0.4.4] - 2025-09-17

- Fix template in pipelex_libraries

## [v0.4.3] - 2025-09-06

### Added

 - Better support for BlackboxAI IDE
 - VS Code extensions recommendations file with Pipelex, Ruff, and MyPy extensions
 - File association for .plx files in VS Code settings
 - Bump `pipelex` to `v0.9.3`: See `Pipelex` changelog [here](https://docs.pipelex.com/changelog/)

## [v0.4.2] - 2025-09-03

- README link to [Pipelex IDE extension](https://open-vsx.org/extension/Pipelex/pipelex)

## [v0.4.1] - 2025-09-02

- Update cursor rules with `PLX` extension naming

## [v0.4.0] - 2025-09-02

- Bump `pipelex` to `v0.9.0`: See `Pipelex` changelog [here](https://docs.pipelex.com/changelog/)
- Changed all the files extension from `.toml` to `.plx`. Need to use pipelex extension.

## [v0.3.2] - 2025-08-27

- Bump `pipelex` to `v0.8.1`: See `Pipelex` changelog [here](https://docs.pipelex.com/changelog/)

## [v0.3.1] - 2025-08-27

- Bump `pipelex` to `v0.8.0`: See `Pipelex` changelog [here](https://docs.pipelex.com/changelog/)

## [v0.3.0] - 2025-08-21

- Bump `pipelex` to `v0.7.0`: See `Pipelex` changelog [here](https://docs.pipelex.com/changelog/)

## [v0.2.9] - 2025-08-02

- Bump `pipelex` to `v0.6.10`: See `Pipelex` changelog [here](https://docs.pipelex.com/changelog/)

### Added
 - Comprehensive Docs/Example Updates: Updated 15+ example files to demonstrate new API patterns
 - New Fashion Variation Pipeline: Complete AI fashion pipeline showcasing multi-step image generation

### Changed
 - Streamlined Pipeline Execution: Replaced complex WorkingMemoryFactory pattern with intuitive input_memory dictionary approach
 - Template Enhancements: Improved Jinja2 template syntax with proper tagging
 - Parameter Consistency: Standardized input parameter naming across pipelines
 - Vertex AI Integration: Updated to stable Gemini model identifiers

## [v0.2.8] - 2025-07-25

- Bump `pipelex` to `v0.6.8`: See `Pipelex` changelog [here](https://docs.pipelex.com/changelog/)

## [v0.2.7] - 2025-07-14

- Tweaked the issue templates

## [v0.2.6] - 2025-07-14

- Bump `pipelex` to `v0.5.2`

### Changed

- Update to Cursor rules
- Renamed Makefile targets like `make doc` to `make docs` for consistency

### Added

- Issue templates

## [v0.2.5] - 2025-07-07

### Core Updates

- Bump `pipelex` to `v0.5.0`

### Changed

- **Terminology Update**: Renamed "samples" to "examples" throughout the codebase for consistency
  - Updated description in `.cursor/rules/samples.mdc`
  - Modified documentation in `AGENTS.md` and `CHANGELOG.md`
  - Updated references in `CONTRIBUTING.md` and `examples/README.md`
  - Changed output directory from `results/samples/` to `results/examples/`
  - Updated environment variable references and function names in `utils/input_utils.py` and `utils/results_utils.py`

- **Working Memory Naming**: Standardized PDF input naming convention
  - Changed `name="pdf"` to `name="ocr_input"` in multiple extraction examples:
    - `extract_dpe.py`
    - `extract_generic.py`
    - `extract_proof_of_purchase.py`
    - `simple_ocr.py`
  - Changed `name="invoice_pdf"` to `name="ocr_input"` in `invoice_extractor.py`

### Added

- **New Advisory Board Example**: Added a sophisticated multi-advisory board consultation system
  - New files in `examples/wip/advisory_board/`:
    - `README.md` - Comprehensive documentation for the advisory board orchestrator
    - `advisory_board.py` - Main example script demonstrating complex pipeline orchestration
  - New pipeline library: `pipelex_libraries/pipelines/wip/advisory_board/advisory_orchestrator.py`
    - Includes structured models for business problems, advisory boards, consensus analysis, and strategic reports
  - Added test coverage in `test_examples.py`

## [v0.2.4] - 2025-06-30

- Bump `pipelex` to `v0.4.11`
- Avoid repetition of llm choice for structured generation in some examples

## [v0.2.3] - 2025-06-30

### Core Updates
- Bump `pipelex` to `v0.4.9`

### New Features

- **External LLM Plugin System**: Example to demonstrate how to use custom LLM integrations with one example based on OpenAI REST API
- Added plugin examples in `examples/using_inference_plugins/`

### Infrastructure 

- **Enhanced GitHub Releases**: Added Sigstore signing and automatic changelog extraction
- **Test Improvements**: Better organization and plugin test coverage


  ## [v0.2.2] - 2025-06-26

- Bump `pipelex` to `v0.4.7`: Full changelog [here](https://docs.pipelex.com/changelog/)
- `pipeline_run_id` is now available in `PipeOutput`

## [v0.2.1] - 2025-06-20

- Bump `pipelex` to `v0.4.4`
- Removed `gemini-1.5` support
- Removed the `images` field from `PipeLLM` - images can now be referenced directly in the `inputs`
- Pytest markers: stop using `llm` and `imgg`. Attach `dry_runnable` marker to some tests
- Change Discord link
- Change Docs link

## [v0.2.0] - 2025-06-16

### Cookbook-Specific Enhancements

### Test Infrastructure

- Reorganized test structure into three categories:
    - `tests/unit/` - Unit tests for individual functions
    - `tests/integration/` - Integration tests for component interactions
    - `tests/e2e/` - End-to-end tests for complete pipeline workflows
- Added `dry_runnable` pytest marker for tests that can run without external API calls
- Updated test configuration to use environment-based pipe run mode selection

### Pipeline Development

- **Prompt template enhancement**: added optional field syntax using `@?` prefix for conditional content insertion
- **Validating pipelines**: updated from `make validate` to direct `pipelex validate` CLI command

### New Examples + Enhancements

- Enhanced tweet optimization pipeline with comprehensive analysis steps
- Updated all examples to demonstrate flowchart generation and cost reporting
- Fixed structural validation in HTML table extraction

### Bug Fixes

- Improved error messages for malformed HTML table structures
- Fixed timezone handling in structured content models
- Resolved test import issues in WIP examples

### Adaptations to Pipelex v0.4.0

The cookbook has been updated to align with breaking changes in Pipelex v0.4.0:

### Concept System Updates

- **Simplified native concepts**: removed `native.` prefix from built-in concepts (e.g., `native.Text` → `Text`, `native.PDF` → `PDF`)
- **Updated concept definitions**: the `refines` attribute in concept definitions now accepts a string for single concept refinement
- **Migrated concept references**:  `concept_code` parameters renamed to `concept_str` in StuffFactory

### Integration Improvements

- **Flowchart generation**: examples now utilize Pipelex's restored Mermaid flowchart generation capability
- **Cost reporting**: added report generation calls to examples to showcase token usage and cost tracking
- **Dry run support: test suite now leverages Pipelex's enhanced dry run configuration for pipeline validation without API calls**

## [v0.1.14] - 2025-06-13

- Cleaned-up the examples and the repository structure
- WIP examples
- Bump pipelex to v0.3.2

## [v0.1.13] - 2025-06-09

- Adapt to the new pipe input handling in Pipelex v0.3.0

## [v0.1.12] - 2025-06-06

- Bumped pipelex to v0.2.14: generalized the new `execute_pipeline` method, enabling to track pipelines from beginning to end with inference cost reporting

## [v0.1.11] - 2025-06-04

### Added

**2 examples for power extraction**:

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
    - simple_ocr.py: use Mistram OCR to extract text from image or pdf
    - pdf_2_power_extractor.py: use OCR in combination with a VLM (Vision Language Model) to catch all the details and reach higher reliability

- WIP Sample for the new execute_mission API: it tracks costs related to a specific mission_id

- Fix for Windows: load text files using explicit "utf-8" encoding

## [v0.1.1] - 2025-05-19

- Polish pyproject metadata

## [v0.1.0] - 2025-05-13

- Initial release 🎉
