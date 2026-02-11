# Extract Invoice

Extract structured invoice information from PDF documents.

## Prerequisites

Before running this example, ensure you have set up your environment. See the [Clone and Install](../../../../README.md#1-clone-and-install) section in the main README.

## Run the pipeline

```bash
pipelex run examples/b_basics/document_extract/extract_invoice/bundle.mthds -i examples/b_basics/document_extract/extract_invoice/inputs.json -L examples/documents
```

## Flowchart

![Flowchart](flowchart.png)

## Expected output

![Expected output](expected_output.png)


## Go further

You can go further by generating the python structures and runner code out of this bundle in order to add validation functions to the python BaseModel.

```bash
pipelex build runner examples/b_basics/document_extract/extract_invoice/bundle.mthds -L examples/documents
```

This will create a new file `examples/b_basics/document_extract/extract_invoice/run_extract_invoice.py` and a `structures` directory containing the python structures.
