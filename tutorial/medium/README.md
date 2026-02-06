# Medium Tutorials

Take your Pipelex skills to the next level.

---

## 1. Model Configuration

Control which LLM to use and how it behaves.

**To change default models and presets**, edit `.pipelex/inference/deck/base_deck.toml`. See the [full list of available models](https://docs.pipelex.com/pre-release/home/5-setup/gateway-models/) and the <!-- PRERELEASE_LINK -->[Inference Backend Configuration](https://docs.pipelex.com/pre-release/home/7-configuration/config-technical/inference-backend-config/) documentation for details.

**File: `1_model_config.plx`**

```plx
domain = "model_config"
description = "Learn how to configure LLM models"
main_pipe = "compare_models"

[pipe]

# Example 1: Default model (uses default config from deck)
[pipe.generate_with_default]
type = "PipeLLM"
description = "Generate text using the default model"
output = "Text"
prompt = """
Write a haiku about coding.
"""

# Example 2: Inline model configuration
[pipe.generate_with_custom_settings]
type = "PipeLLM"
description = "Generate text with custom temperature"
output = "Text"
model = { model = "best-claude", temperature = 0.9 }
prompt = """
Write a creative haiku about coding.
"""

# Example 3: Using a preset
[pipe.generate_with_preset]
type = "PipeLLM"
description = "Generate text using a preset"
output = "Text"
model = "$writing-creative"
prompt = """
Write a creative haiku about coding.
"""

# Compare all three approaches
[pipe.compare_models]
type = "PipeSequence"
description = "Compare different model configurations"
output = "Text"
steps = [
    { pipe = "generate_with_default", result = "default_result" },
    { pipe = "generate_with_custom_settings", result = "custom_result" },
    { pipe = "generate_with_preset", result = "preset_result" },
    { pipe = "format_comparison", result = "comparison" },
]

[pipe.format_comparison]
type = "PipeCompose"
description = "Format the comparison results"
inputs = { default_result = "Text", custom_result = "Text", preset_result = "Text" }
output = "Text"
template = """
# Model Configuration Comparison

## 1. Default Model (no config)
$default_result

## 2. Custom Settings (temperature = 0.9)
$custom_result

## 3. Preset (writing-creative)
$preset_result
"""
```

**What you need to know:**
- `model = { model = "...", temperature = 0.9 }` - Inline configuration
- `model = "preset_name"` - Use a predefined preset from your deck: Leanr more here: [LLM Presets](https://docs.pipelex.com/latest/home/7-configuration/config-technical/inference-backend-config/)
- Temperature: 0.0 = deterministic, 1.0 = creative
- Presets and aliases are defined in `.pipelex/inference/deck/base_deck.toml`

**Run it:**
```bash
pipelex run tutorial/medium/1_model_config.plx
```

---

## 2. Batch Processing

Process a list of items one by one (in parallel behind the scenes).

**File: `2_batch_processing.plx`**

```plx
domain = "batch_processing"
description = "Learn how to process items in batches"
main_pipe = "batch_write_summaries"

[concept]

[concept.Topic]
description = "A topic to write about"
refines = "Text"

[pipe]

# Step 1: Generate a list of topics
[pipe.generate_topics]
type = "PipeLLM"
description = "Generate a list of topics"
output = "Topic[3]"
prompt = """
Generate 3 interesting topics for short blog posts about technology.
Just the topic titles, nothing else.
"""

# Step 2: Process each topic (this will be batched)
[pipe.write_summary]
type = "PipeLLM"
description = "Write a summary for a single topic"
inputs = { topic = "Topic" }
output = "Text"
prompt = """
Write a 2-sentence summary for a blog post about:

$topic
"""

# Step 3: Combine results
[pipe.format_results]
type = "PipeCompose"
description = "Format all summaries"
inputs = { summaries = "Text[]" }
output = "Text"
template = """
# Blog Post Summaries

@summaries
"""

# Main pipeline using batch_over
[pipe.batch_write_summaries]
type = "PipeSequence"
description = "Generate topics and write summaries for each"
output = "Text"
steps = [
    { pipe = "generate_topics", result = "topics" },
    { pipe = "write_summary", batch_over = "topics", batch_as = "topic", result = "summaries" },
    { pipe = "format_results", result = "final_output" },
]
```

**What you need to know:**
- `batch_over = "topics"` - The list to iterate over
- `batch_as = "topic"` - Name for each item in the loop
- Each item is processed in parallel automatically
- Result is a list of outputs

**Run it:**
```bash
pipelex run tutorial/medium/2_batch_processing.plx
```

---

## 3. Parallel Execution

Run independent pipes at the same time.

**File: `3_parallel_execution.plx`**

```plx
domain = "parallel_execution"
description = "Learn how to run pipes in parallel"
main_pipe = "generate_poems_parallel"

[pipe]

# Three independent pipes that can run in parallel
[pipe.generate_haiku]
type = "PipeLLM"
description = "Generate a haiku"
output = "Text"
prompt = """
Write a haiku about the ocean.
"""

[pipe.generate_limerick]
type = "PipeLLM"
description = "Generate a limerick"
output = "Text"
prompt = """
Write a limerick about a programmer.
"""

[pipe.generate_sonnet_excerpt]
type = "PipeLLM"
description = "Generate a sonnet excerpt"
output = "Text"
prompt = """
Write the first 4 lines of a sonnet about nature.
"""

# Run all three in parallel
[pipe.generate_poems_parallel]
type = "PipeParallel"
description = "Generate different poem types in parallel"
output = "Dynamic"
parallels = [
    { pipe = "generate_haiku", result = "haiku" },
    { pipe = "generate_limerick", result = "limerick" },
    { pipe = "generate_sonnet_excerpt", result = "sonnet" },
]
add_each_output = true
```

**What you need to know:**
- `PipeParallel` runs all pipes at the same time
- `parallels` - List of pipes to run in parallel
- `add_each_output = true` - Add each result to working memory
- Use this when pipes don't depend on each other

**Run it:**
```bash
pipelex run tutorial/medium/3_parallel_execution.plx
```

---

## Summary

| Feature | How to use |
|---------|------------|
| Custom model | `model = { model = "...", temperature = 0.5 }` |
| Preset | `model = "preset_name"` |
| Batch processing | `batch_over = "list"`, `batch_as = "item"` |
| Parallel execution | `PipeParallel` with `parallels = [...]` |

**Next:** Explore the [examples](../../examples/) for real-world use cases!
