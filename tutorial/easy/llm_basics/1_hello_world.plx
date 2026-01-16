domain = "hello_world"
description = "Your first Pipelex pipeline"

[pipe]

[pipe.hello_world]
type = "PipeLLM"
description = "Generate a creative story idea"
output = "Text"
prompt = """
Generate a one-paragraph creative story idea about a robot learning to paint.
"""
