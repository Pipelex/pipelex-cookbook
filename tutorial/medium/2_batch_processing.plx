domain = "batch_processing"
description = "Learn how to process items in batches"

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
