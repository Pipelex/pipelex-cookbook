# Extract DPE (Diagnostic de Performance Énergétique)

Extract energy performance diagnostic information from French DPE documents which is a PDF file.

## Prerequisites

Before running this example, ensure you have set up your environment. See the [Clone and Install](../../../../README.md#1-clone-and-install) section in the main README.

## Run the pipeline

```bash
pipelex run bundle examples/b_basics/document_extract/extract_dpe/
```

## Flowchart

![Flowchart](flowchart.png)

## Expected output

![Expected output](expected_output.png)


## Go further

You can go further by generating the python structures and runner code out of this bundle in order to add validation functions to the python BaseModel. 

```bash
pipelex build runner bundle examples/b_basics/document_extract/extract_dpe/bundle.mthds
```

This will create a new file `examples/b_basics/document_extract/extract_dpe/run_power_extractor_dpe.py` and a `structures` directory containing the python structures.