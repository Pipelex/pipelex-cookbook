# Pipelex Tutorials

Welcome to the Pipelex tutorials! Learn how to build AI pipelines step by step.

> **Note**: The easiest way to make a method is to ask your coding agent, with the Pipelex plugin, as the cookbook's [front page](../README.md#try-a-method-in-a-minute) shows. These tutorials teach you to write one by hand, and to run it on your own machine.

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
pipelex init
pipelex doctor
```

`pipelex init` writes your `~/.pipelex` configuration and offers to install the editor extension; `pipelex doctor` reports what is configured and what is missing. Some providers and features need an extra, such as the document extraction of the `3_document_qa` lesson: [Run It Yourself](https://docs.pipelex.com/latest/get-started/run-it-yourself/) lists them.

**2. Give the runtime access to models**

Bring your own provider keys, or run models locally: [Configure AI Providers](https://docs.pipelex.com/latest/get-started/configure-ai-providers/) says how.

**3. Get the tutorials**

```bash
git clone https://github.com/Pipelex/pipelex-cookbook.git
cd pipelex-cookbook
```

**4. Run your first tutorial**

```bash
pipelex run bundle tutorial/easy/llm_basics/1_hello_world.mthds
```

**The editor extension** highlights `.mthds` files and draws their flowcharts: the [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=pipelex.pipelex), or the [Open VSX Registry](https://open-vsx.org/extension/Pipelex/pipelex) for Cursor, Windsurf and other VS Code forks. `pipelex init` offers to install it when it detects your IDE.

## Key Concepts

Every `.mthds` pipeline file needs:
- `domain` - A unique name for your pipeline
- `main_pipe` - Which pipe to run by default (required when CLI doesn't specify a pipe)
- `[pipe]` section with your pipe definitions
