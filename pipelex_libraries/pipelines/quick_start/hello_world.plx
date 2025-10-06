

domain = "quick_start"
description = "Discovering Pipelex"

[pipe]
[pipe.hello_world]
type = "PipeLLM"
description = "Write text about Hello World."
output = "Text"
llm = { llm_handle = "gpt-4o-mini", temperature = 0.9, max_tokens = "auto" }
prompt = """
Write a haiku about Hello World.
"""

