

domain = "hello_plugin"
description = "Using an LLM Plugin"

[pipe]
[pipe.hello_plugin]
type = "PipeLLM"
description = "Write text about Hello World."
output = "Text"
llm = { llm_handle = "llm_plugin_example_using_openai", temperature = 0.5 }
prompt = """
Write a haiku about Hello World.
"""

