# Discord Newsletter

Create newsletters from Discord channel content by summarizing messages and organizing them.

The pipes and concepts come from the cookbook's [`discord_newsletter`](../../../methods/discord_newsletter/) method, which anyone can also run by address on the hosted Pipelex API.

## Prerequisites

Before running this example, ensure you have set up your environment. See the [Clone and Install](../../../README.md#1-clone-and-install) section in the main README.

## What This Example Demonstrates

This example shows how to load data from an **arbitrary JSON file** and convert it into conceptual input for a Pipelex pipeline. This pattern is useful when:

- You have existing data in JSON format from external sources (APIs, exports, etc.)
- You want to process that data through a pipeline without reformatting it into the standard `inputs.json` format
- You need to validate and transform the data before passing it to the pipeline

The key steps are:
1. Load raw JSON data from any source
2. Pass the items as the content of an input that names their concept, `discord_newsletter.DiscordChannelUpdate`
3. Let the runtime validate each item against the structure the bundle declares for that concept

## Run the pipeline

From the root of the repository, run the Python script that loads the Discord export JSON and generates the newsletter:

```bash
python examples/wip/discord_newsletter/run_discord_newsletter.py
```

The script loads the bundle from `methods/discord_newsletter/` and the Discord channel data from `assets/discord_newsletter/discord_extract.json`, processes it through the pipeline, and writes the newsletter's HTML under `results/examples/discord_newsletter/`.
