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

**2. Set your provider API keys**

Pipelex runs your methods with your own provider credentials. Copy `.env.example` to `.env` and fill in the key of every provider you intend to use, or set a single [OpenRouter](https://openrouter.ai) key to reach models from many providers at once:

```bash
OPENAI_API_KEY=your_openai_key_here
# or, for many providers with one key:
OPENROUTER_API_KEY=your_openrouter_key_here
```

A key alone is not enough for any provider other than OpenRouter: its backend also has to be switched on and routed to. See [Configure AI Providers](https://docs.pipelex.com/latest/get-started/configure-ai-providers/).

Rather not hold provider keys at all? Sign up at [app.pipelex.com](https://app.pipelex.com/), create a Pipelex API key, and run your methods on the hosted Pipelex API instead.

**3. Run your first tutorial**

```bash
pipelex run bundle tutorial/easy/llm_basics/1_hello_world.mthds
```

## Key Concepts

Every `.mthds` pipeline file needs:
- `domain` - A unique name for your pipeline
- `main_pipe` - Which pipe to run by default (required when CLI doesn't specify a pipe)
- `[pipe]` section with your pipe definitions
