# Sample Pipelines to show off Pipelex capabilities

The pipelines in this folder demonstrate various Pipelex capabilities. Each example
includes an `inputs.json` file with sample inputs that can be used to run the pipeline.

## Directory Structure

```
examples/
├── a_quick_start/         # Getting started tutorials
├── b_basics/              # Core functionality examples
│   └── document_extract/  # Document extraction examples
│       ├── extract_invoice/
│       ├── extract_proof_of_purchase/
│       └── extract_table/
├── c_advanced/            # Advanced features
│   ├── crewai_with_pipelex_tools/
│   └── using_inference_plugins/
└── wip/                   # Work in progress (not stable)
```

## Quick Start Examples (`a_quick_start/`)

- `hello_world.mthds` - Your first Pipelex pipeline
- `summarize.mthds` - Multi-step text summarization with structured output

## Document Extraction Examples (`b_basics/document_extract/`)

- [Gantt chart extraction](../methods/extract_gantt/) - Extract structured data from Gantt chart images, now a method runnable by address in `methods/extract_gantt/`
- `extract_invoice/` - Extract structured data from invoice documents
- `extract_table/` - Extract HTML tables from image screenshots
- `extract_proof_of_purchase/` - Extract key information from receipts and invoices
- [DPE extraction](../methods/extract_dpe/) and [generic document extraction](../methods/extract_generic/) are now methods runnable by address, in `methods/`

## Advanced Examples (`c_advanced/`)

- `crewai_with_pipelex_tools/` - A CrewAI crew calling the [research report method](../methods/research_report/) as a tool
- [Synthetic data generation](../methods/gen_synthetic_data/) is now a method runnable by address, in `methods/`

## Work in Progress (`wip/`)

The `wip/` folder contains experimental pipelines that are not yet stable.

## Running the Examples

Run any example from the repository root using the CLI:

```bash
# Quick start - Hello World (no inputs needed)
pipelex run bundle examples/a_quick_start/hello_world.mthds

# Quick start - Summarization with inputs
pipelex run bundle examples/a_quick_start/summarize.mthds --pipe summarize_with_structure -i examples/a_quick_start/inputs.json

# Document extraction - Invoice
pipelex run bundle examples/b_basics/document_extract/extract_invoice/bundle.mthds -i examples/b_basics/document_extract/extract_invoice/inputs.json

# Document extraction - Table
pipelex run bundle examples/b_basics/document_extract/extract_table/bundle.mthds -i examples/b_basics/document_extract/extract_table/inputs.json
```

Results will be saved as JSON files in the current directory (or specify `-o path/to/output.json`).

## Prerequisites

Before running these examples, make sure you have:
1. Created and activated a virtual environment
2. Installed the dependencies

See the [Clone and Install](../README.md#1-clone-and-install) section in the main README for setup instructions.
