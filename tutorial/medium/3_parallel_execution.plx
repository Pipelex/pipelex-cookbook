domain = "parallel_execution"
description = "Learn how to run pipes in parallel"
main_pipe = "create_poetry_collection"

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

# Combine the parallel results into a single output
[pipe.format_poems]
type = "PipeCompose"
description = "Combine all poems into a collection"
inputs = { haiku = "Text", limerick = "Text", sonnet = "Text" }
output = "Text"
template = """
# Poetry Collection

## Haiku
$haiku

## Limerick
$limerick

## Sonnet (excerpt)
$sonnet
"""

# Main pipeline: run parallel, then combine
[pipe.create_poetry_collection]
type = "PipeSequence"
description = "Create a collection of poems using parallel execution"
output = "Text"
steps = [
    { pipe = "generate_poems_parallel", result = "poems" },
    { pipe = "format_poems", result = "collection" },
]
