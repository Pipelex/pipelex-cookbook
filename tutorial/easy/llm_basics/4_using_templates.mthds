domain = "using_templates"
description = "Format output with templates"
main_pipe = "create_story_document"

[pipe]

# First pipe: Generate a story idea
[pipe.template_generate_idea]
type = "PipeLLM"
description = "Generate a creative story idea"
output = "Text"
prompt = """
Generate a one-paragraph creative story idea about a robot learning to paint.
"""

# Second pipe: Expand the story idea
[pipe.template_expand_idea]
type = "PipeLLM"
description = "Expand a story idea into a detailed outline"
inputs = { story_idea = "Text" }
output = "Text"
prompt = """
Take this story idea and expand it into a 3-act outline:

@story_idea

Provide a brief description for each act.
"""

# Third pipe: Format the output using a template
[pipe.format_document]
type = "PipeCompose"
description = "Format the story into a nice document"
inputs = { story_idea = "Text", story_outline = "Text" }
output = "Text"
template = """
# Story Document

## Original Idea

$story_idea

## Story Outline

$story_outline

---
*Generated with Pipelex*
"""

# Full pipeline: Generate, expand, and format
[pipe.create_story_document]
type = "PipeSequence"
description = "Generate, expand, and format a story"
output = "Text"
steps = [
    { pipe = "template_generate_idea", result = "story_idea" },
    { pipe = "template_expand_idea", result = "story_outline" },
    { pipe = "format_document", result = "final_document" },
]
