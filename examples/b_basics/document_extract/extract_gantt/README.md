# Extract Gantt Chart

Extract structured data from Gantt chart images.

## Run the pipeline

```bash
pipelex run examples/b_basics/document_extract/extract_gantt/bundle.plx -i examples/b_basics/document_extract/extract_gantt/inputs.json
```

## Flowchart

![Flowchart](flowchart.png)

## Expected output

![Expected output](expected_output.png)


## Go further

You can go further by generating the python structures and runner code out of this bundle in order to add validation functions to the python BaseModel.

```bash
pipelex build runner examples/b_basics/document_extract/extract_gantt/bundle.plx
```

This will create a new file `examples/b_basics/document_extract/extract_gantt/run_extract_gantt_by_steps.py` and a `structures` directory containing the python structures.
