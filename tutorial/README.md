# Pipelex Tutorials

Welcome to the Pipelex tutorials! Learn how to build AI pipelines step by step.


> **Note**: The easiest way to create pipelines is with the [Pipe Builder](https://docs.pipelex.com/home/9-tools/pipe-builder/). These tutorials teach you the fundamentals by writing pipelines manually.

## Tutorials

### [Easy](./easy/README.md)

1. **[LLM Basics](./easy/llm_basics/README.md)** - Your first steps with Pipelex
2. **[Structured Data](./easy/structured_data/README.md)** - Get structured objects from LLMs

### [Medium](./medium/README.md)

1. **[Model Configuration](./medium/README.md)** - Control which LLM to use and how
2. **[Batch Processing](./medium/README.md)** - Process lists of items efficiently
3. **[Parallel Execution](./medium/README.md)** - Run independent tasks at the same time

## Getting Started

**1. Install Pipelex**

```bash
uv tool install pipelex
```

**2. Get your API key**

Sign up at [app.pipelex.com](https://app.pipelex.com) to get **free API credits** with access to all models.

Add your key to `.env`:
```bash
PIPELEX_GATEWAY_API_KEY=your_api_key_here
```

**3. Run your first tutorial**

```bash
pipelex run bundle tutorial/easy/llm_basics/1_hello_world.mthds
```

## Key Concepts

Every `.mthds` pipeline file needs:
- `domain` - A unique name for your pipeline
- `main_pipe` - Which pipe to run by default (required when CLI doesn't specify a pipe)
- `[pipe]` section with your pipe definitions
