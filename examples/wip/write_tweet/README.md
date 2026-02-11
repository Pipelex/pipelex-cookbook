# Tech Tweet Optimizer

A pipeline for optimizing tech tweets using Twitter/X best practices, helping avoid common startup communication pitfalls.

## Prerequisites

Before running this example, ensure you have set up your environment. See the [Clone and Install](../../../README.md#1-clone-and-install) section in the main README.

## Run the pipeline

```bash
pipelex run examples/wip/write_tweet/tech_tweet.mthds -i examples/wip/write_tweet/inputs.json
```

## What it Does

The Tech Tweet Optimizer:
1. **Analyzes** a draft tweet for common issues (fluffiness, cringiness, humblebragging, vagueness)
2. **Scores** each issue on a 1-5 scale with specific guidance
3. **Rewrites** the tweet to be more engaging while keeping the core message

## Key Features Demonstrated

- **PipeSequence**: Two-step pipeline (analyze → optimize)
- **LLM Presets**: Uses specialized presets for analysis and writing
- **Style Reference**: Takes a writing style example as input to guide the output

## Inputs

- `draft_tweet`: The original tweet to optimize
- `writing_style`: A reference style example to guide the rewrite
