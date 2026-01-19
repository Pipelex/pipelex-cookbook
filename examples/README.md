# Sample Pipelines to show off Pipelex capabilities

The scripts in this folder demonstrate various Pipelex pipelines and capabilities. They
rely on helper functions in `cookbook/utils` and write their results to the
`results/examples/` directory.

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

- `hello_world.py` - Your first Pipelex pipeline
- `simple_ocr.py` - Basic OCR capabilities on PDF documents
- `summarize_2_steps.py` - Multi-step text summarization
- `summarize_1_structured.py` - Summarization with structured output

## Document Extraction Examples (`b_basics/document_extract/`)

- `extract_gantt/` - Extract structured data from Gantt chart images
- `extract_invoice/` - Extract structured data from invoice documents
- `extract_table/` - Extract HTML tables from image screenshots
- `extract_proof_of_purchase/` - Extract key information from receipts and invoices
- `extract_dpe/` - Extract information from DPE (Diagnostic de Performance Énergétique) documents
- `extract_generic/` - Generic document extraction pipeline for various document types

## Advanced Examples (`c_advanced/`)

- `gen_synthetic_data/` - Generate synthetic data based on schemas
- `using_inference_plugins/` - Custom inference plugin integration

## Work in Progress (`wip/`)

The `wip/` folder contains experimental pipelines that are not yet stable.

## Running the Examples

Run any example from the repository root:

```bash
# Quick start
python examples/a_quick_start/hello_world.py

# Document extraction
python examples/b_basics/document_extract/extract_gantt/extract_gantt.py
python examples/b_basics/document_extract/extract_invoice/extract_invoice.py

# Advanced features
python examples/c_advanced/gen_synthetic_data/synth.py
```

Each example includes detailed comments explaining the pipeline construction and configuration.
Results will be saved in the `results/examples/` directory for inspection.

## Prerequisites

Make sure you have installed all required dependencies and have the necessary API keys
configured for any LLM or OCR services used in the examples. Refer to the main README
for setup instructions.
