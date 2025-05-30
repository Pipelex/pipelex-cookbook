# Changelog

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
