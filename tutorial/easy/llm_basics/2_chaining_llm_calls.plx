domain = "chaining_llm_calls"
description = "Chain multiple LLM calls together"

[pipe]

# First pipe: Generate a story idea
[pipe.generate_idea]
type = "PipeLLM"
description = "Generate a creative story idea"
output = "Text"
prompt = """
Generate a one-paragraph creative story idea about a robot learning to paint.
"""

# Second pipe: Expand the story idea (uses result from first pipe)
[pipe.expand_idea]
type = "PipeLLM"
description = "Expand a story idea into a detailed outline"
inputs = { story_idea = "Text" }
output = "Text"
prompt = """
Take this story idea and expand it into a 3-act outline:

@story_idea

Provide a brief description for each act.
"""

# PipeSequence: Chain the two pipes together
[pipe.generate_and_expand]
type = "PipeSequence"
description = "Generate a story idea then expand it"
output = "Text"
steps = [
    { pipe = "generate_idea", result = "story_idea" },
    { pipe = "expand_idea", result = "story_outline" },
]
