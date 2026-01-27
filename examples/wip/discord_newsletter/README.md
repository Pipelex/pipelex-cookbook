# Discord Newsletter

Create newsletters from Discord channel content by summarizing messages and organizing them.

## Prerequisites

Before running this example, ensure you have set up your environment. See the [Clone and Install](../../../README.md#1-clone-and-install) section in the main README.

## Run the pipeline

```bash
pipelex run examples/wip/discord_newsletter/bundle.plx -i examples/wip/discord_newsletter/inputs.json
```

## Flowchart

![Flowchart](flowchart.png)

## Expected output

![Expected output](expected_output.png)


## Go further

You can go further by generating the python structures and runner code out of this bundle in order to add validation functions to the python BaseModel.

```bash
pipelex build runner examples/wip/discord_newsletter/bundle.plx
```

This will create a new file `examples/wip/discord_newsletter/run_discord_newsletter.py` and a `structures` directory containing the python structures.
