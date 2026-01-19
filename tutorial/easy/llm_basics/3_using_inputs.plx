domain = "using_inputs"
description = "Learn how to pass inputs to your pipeline"

[pipe]

# A pipe that takes an input and uses it
[pipe.write_about_topic]
type = "PipeLLM"
description = "Write a short paragraph about a given topic"
inputs = { topic = "Text" }
output = "Text"
prompt = """
Write a short, engaging paragraph about the following topic:

$topic

Keep it under 100 words.
"""
