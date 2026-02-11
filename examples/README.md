# Sample Pipelines to show off Pipelex capabilities

The pipelines in this folder demonstrate various Pipelex capabilities. Each example
includes an `inputs.json` file with sample inputs that can be used to run the pipeline.

## Directory Structure

```
examples/
├── a_quick_start/         # Getting started tutorials
├── b_basics/              # Core functionality examples
│   └── document_extract/  # Document extraction examples
│       ├── extract_dpe/
│       ├── extract_gantt/
│       ├── extract_generic/
│       ├── extract_invoice/
│       ├── extract_proof_of_purchase/
│       └── extract_table/
├── c_advanced/            # Advanced features
│   ├── gen_synthetic_data/
│   └── using_inference_plugins/
└── wip/                   # Work in progress (not stable)
```

## Quick Start Examples (`a_quick_start/`)

- `hello_world.mthds` - Your first Pipelex pipeline
- `summarize.mthds` - Multi-step text summarization with structured output

## Document Extraction Examples (`b_basics/document_extract/`)

- `extract_gantt/` - Extract structured data from Gantt chart images
- `extract_invoice/` - Extract structured data from invoice documents
- `extract_table/` - Extract HTML tables from image screenshots
- `extract_proof_of_purchase/` - Extract key information from receipts and invoices
- `extract_dpe/` - Extract information from DPE (Diagnostic de Performance Énergétique) documents
- `extract_generic/` - Generic document extraction pipeline for various document types

## Advanced Examples (`c_advanced/`)

- `gen_synthetic_data/` - Generate synthetic data based on schemas

## Work in Progress (`wip/`)

The `wip/` folder contains experimental pipelines that are not yet stable.

## Running the Examples

Run any example from the repository root using the CLI:

```bash
# Quick start - Hello World (no inputs needed)
pipelex run examples/a_quick_start/hello_world.mthds

# Quick start - Summarization with inputs
pipelex run examples/a_quick_start/summarize.mthds --pipe summarize_with_structure -i examples/a_quick_start/inputs.json

# Document extraction - Gantt chart
pipelex run examples/b_basics/document_extract/extract_gantt/bundle.mthds -i examples/b_basics/document_extract/extract_gantt/inputs.json

# Document extraction - Invoice
pipelex run examples/b_basics/document_extract/extract_invoice/bundle.mthds -i examples/b_basics/document_extract/extract_invoice/inputs.json

# Document extraction - Table
pipelex run examples/b_basics/document_extract/extract_table/bundle.mthds -i examples/b_basics/document_extract/extract_table/inputs.json

# Advanced features - Synthetic data generation
pipelex run examples/c_advanced/gen_synthetic_data/bundle.mthds -i examples/c_advanced/gen_synthetic_data/inputs.json
```

Results will be saved as JSON files in the current directory (or specify `-o path/to/output.json`).

## Prerequisites

Before running these examples, make sure you have:
1. Created and activated a virtual environment
2. Installed the dependencies

See the [Clone and Install](../README.md#1-clone-and-install) section in the main README for setup instructions.
