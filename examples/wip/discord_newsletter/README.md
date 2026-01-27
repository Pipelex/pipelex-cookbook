# Discord Newsletter

Create newsletters from Discord channel content by summarizing messages and organizing them.

## Prerequisites

Before running this example, ensure you have set up your environment. See the [Clone and Install](../../../README.md#1-clone-and-install) section in the main README.

## What This Example Demonstrates

This example shows how to load data from an **arbitrary JSON file** and convert it into conceptual input for a Pipelex pipeline. This pattern is useful when:

- You have existing data in JSON format from external sources (APIs, exports, etc.)
- You want to process that data through a pipeline without reformatting it into the standard `inputs.json` format
- You need to validate and transform the data before passing it to the pipeline

The key steps are:
1. Load raw JSON data from any source
2. Validate and convert it to StructuredContent (Pydantic) objects
3. Pass those objects directly to the pipeline as typed input

## Run the pipeline

Run the Python script that loads the Discord export JSON and generates the newsletter:

```bash
python examples/wip/discord_newsletter/run_discord_newsletter.py
```

The script loads Discord channel data from `assets/discord_newsletter/discord_extract.json` and processes it through the pipeline.

## Flowchart

![Flowchart](flowchart.png)

## Expected output

![Expected output](expected_output.png)

