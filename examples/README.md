# Sample Pipelines to show off Pipelex capabilities

The scripts in this folder demonstrate various Pipelex pipelines and capabilities. They
rely on helper functions in `cookbook/utils` and write their results to the
`results/samples/` directory.

The folder wip contains work in progress. The pipelines in this folder are not stable.

## Available Examples

- `expense_report.py` processes invoices and an expense report to extract
  structured information.
- `extract_gantt.py` extracts a gantt chart from an image.
- `extract_table.py` extracts an HTML table from an image screenshot.
- `extract_proof_of_purchase.py` extracts key information from proof of purchase documents
  like receipts and invoices.
- `extract_dpe.py` demonstrates extraction of information from DPE (Diagnostic de Performance
  Énergétique) documents.
- `extract_generic.py` shows how to build a generic document extraction pipeline that can
  handle various document types.
- `invoice_extractor.py` specializes in extracting structured data from invoice documents,
  including line items, totals, and vendor information.
- `simple_ocr.py` demonstrates basic OCR capabilities on PDF documents,
  extracting text and images from each page.
- `retrieve_then_answer.py` showcases a RAG (Retrieval-Augmented Generation) pipeline
  that first retrieves relevant information and then answers questions about documents.

## Running the Examples

Run any sample from the repository root, for example:

```bash
python examples/extract_table.py
```

Each example includes detailed comments explaining the pipeline construction and configuration.
The results will be saved in the `results/samples/` directory for inspection.

## Prerequisites

Make sure you have installed all required dependencies and have the necessary API keys
configured for any LLM or OCR services used in the examples. Refer to the main README
for setup instructions.
