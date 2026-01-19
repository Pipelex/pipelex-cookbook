# Medium Tutorials

Take your Pipelex skills to the next level.

---

## 1. Model Configuration

Control which LLM to use and how it behaves.

**To change default models and presets**, edit `.pipelex/inference/deck/base_deck.toml`. See the [full list of available models](https://docs.pipelex.com/0.18.0b1/home/5-setup/gateway-models/) and the [Inference Backend Configuration](https://docs.pipelex.com/latest/home/7-configuration/config-technical/inference-backend-config/) documentation for details.

**File: `1_model_config.plx`**

### Default (uses default config from deck)

```plx
[pipe.generate_text]
type = "PipeLLM"
output = "Text"
prompt = "Write a haiku."
```

### Inline settings

```plx
[pipe.generate_creative]
type = "PipeLLM"
output = "Text"
model = { model = "base-claude", temperature = 0.9 }
prompt = "Write a creative haiku."
```

### Using a preset

```plx
[pipe.generate_with_preset]
type = "PipeLLM"
output = "Text"
model = "llm_for_creative_writing"
prompt = "Write a creative haiku."
```

**What you need to know:**
- `model = { model = "...", temperature = 0.9 }` - Inline configuration
- `model = "preset_name"` - Use a predefined preset from your deck
- Temperature: 0.0 = deterministic, 1.0 = creative
- Presets and aliases are defined in `.pipelex/inference/deck/base_deck.toml`

**Run it:**
```bash
python tutorial/medium/1_model_config.py
```

---

## 2. Batch Processing

Process a list of items one by one (in parallel behind the scenes).

**File: `2_batch_processing.plx`**

```plx
# Generate a list of topics
[pipe.generate_topics]
type = "PipeLLM"
output = "Topic[3]"
prompt = "Generate 3 blog topics."

# Process a single topic
[pipe.write_summary]
type = "PipeLLM"
inputs = { topic = "Topic" }
output = "Text"
prompt = "Write a summary for: $topic"

# Batch over the list
[pipe.batch_pipeline]
type = "PipeSequence"
output = "Text"
steps = [
    { pipe = "generate_topics", result = "topics" },
    { pipe = "write_summary", batch_over = "topics", batch_as = "topic", result = "summaries" },
]
```

**What you need to know:**
- `batch_over = "topics"` - The list to iterate over
- `batch_as = "topic"` - Name for each item in the loop
- Each item is processed in parallel automatically
- Result is a list of outputs

**Run it:**
```bash
python tutorial/medium/2_batch_processing.py
```

---

## 3. Parallel Execution

Run independent pipes at the same time.

**File: `3_parallel_execution.plx`**

```plx
[pipe.task_a]
type = "PipeLLM"
output = "Text"
prompt = "Write a haiku."

[pipe.task_b]
type = "PipeLLM"
output = "Text"
prompt = "Write a limerick."

[pipe.run_parallel]
type = "PipeParallel"
output = "Dynamic"
parallels = [
    { pipe = "task_a", result = "haiku" },
    { pipe = "task_b", result = "limerick" },
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
python tutorial/medium/3_parallel_execution.py
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
