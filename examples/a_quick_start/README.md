# Quick Start Examples

This folder contains simple pipelines that demonstrate the basics of running Pipelex.

## Hello World

A minimal pipeline that generates text.

### Run the pipeline

```bash
pipelex run examples/a_quick_start/hello_world.plx
```

### Expected output

![Expected output](expected_output.png)

### Flowchart

<!-- Pipeline flowchart will be added here -->

---

## Summarize

Text summarization pipelines with structured output.

### Run the pipeline

```bash
# Summarization with structured output
pipelex run examples/a_quick_start/summarize.plx --pipe summarize_with_structure -i examples/a_quick_start/inputs.json

# Multi-step summarization
pipelex run examples/a_quick_start/summarize.plx --pipe summarize_by_steps -i examples/a_quick_start/inputs.json
```

### Expected output

![Expected output](expected_output.png)

### Flowchart

<!-- Pipeline flowchart will be added here -->
