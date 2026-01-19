# Pipelex Tutorials

Welcome to the Pipelex tutorials! Learn how to build AI pipelines step by step.

> **Note**: The easiest way to create pipelines is with the [Pipe Builder](https://docs.pipelex.com/latest/home/9-tools/pipe-builder/). These tutorials teach you the fundamentals by writing pipelines manually.

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
pip install pipelex
# or
uv pip install pipelex
```

**2. Get your API key**

Sign up at [app.pipelex.com](https://app.pipelex.com) to get **$20 free API credit** with access to all models.

Add your key to `.env`:
```bash
PIPELEX_API_KEY=your_api_key_here
```

**3. Run your first tutorial**

```bash
python tutorial/easy/llm_basics/1_hello_world.py
```
