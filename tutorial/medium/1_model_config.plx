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
model = { model = "base-claude", temperature = 0.9 }
prompt = """
Write a creative haiku about coding.
"""

# Example 3: Using a preset
[pipe.generate_with_preset]
type = "PipeLLM"
description = "Generate text using a preset"
output = "Text"
model = "llm_for_creative_writing"
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

## 3. Preset (llm_for_creative_writing)
$preset_result
"""
