# Tutorial 1: Simple LLM Calls

In this tutorial, you'll learn how to:
- Create a simple PipeLLM without inputs
- Chain multiple LLM calls using PipeSequence
- Use PipeCompose for templated outputs

> **Disclaimer**: The easiest way to create a pipe is to use the [Pipe Builder](https://docs.pipelex.com/home/9-tools/pipe-builder/). However, in this tutorial we write pipelines manually to understand the concepts.

---

## Step 1: Your First PipeLLM

Let's start with the simplest possible pipeline: an LLM that generates text without any input.

```plx
domain = "tutorial_simple"
description = "Tutorial: Simple LLM calls"

[pipe.generate_story_idea]
type = "PipeLLM"
description = "Generate a creative story idea"
output = "Text"
prompt = """
Generate a one-paragraph creative story idea about a robot learning to paint.
"""
```

**What's happening here?**
- `domain` - Names your pipeline domain
- `type = "PipeLLM"` - This pipe uses a Large Language Model
- `output = "Text"` - The output is plain text
- `prompt` - The instruction for the LLM

---

## Step 2: Chaining LLM Calls with PipeSequence

What if you want to make **two LLM calls in sequence**, where the second uses the result of the first?

This is where **PipeSequence** comes in - a **Pipe Controller** that orchestrates multiple pipes!

```plx
[pipe.expand_story_idea]
type = "PipeLLM"
description = "Expand a story idea into a detailed outline"
inputs = { story_idea = "Text" }
output = "Text"
prompt = """
Take this story idea and expand it into a 3-act outline:

@story_idea

Provide a brief description for each act.
"""

[pipe.generate_and_expand_story]
type = "PipeSequence"
description = "Generate a story idea and expand it into an outline"
output = "Text"
steps = [
    { pipe = "generate_story_idea", result = "story_idea" },
    { pipe = "expand_story_idea", result = "story_outline" },
]
```

**What's happening here?**
- `PipeSequence` runs pipes in order
- Each step's `result` is stored in the working memory
- The second pipe `expand_story_idea` uses `story_idea` from the first step
- `inputs` must be declared for pipes that need external data

---

## Step 3: Templated Output with PipeCompose

What if you want to create a **formatted summary** using a template? Use **PipeCompose**!

```plx
[pipe.compose_story_document]
type = "PipeCompose"
description = "Compose a formatted story document"
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

[pipe.full_story_pipeline]
type = "PipeSequence"
description = "Generate, expand, and format a story"
output = "Text"
steps = [
    { pipe = "generate_story_idea", result = "story_idea" },
    { pipe = "expand_story_idea", result = "story_outline" },
    { pipe = "compose_story_document", result = "final_document" },
]
```

**What's happening here?**
- `PipeCompose` uses Jinja2 templates to format text
- `$variable` inserts content inline (for short text)
- `@variable` inserts content as a block (for longer text)
- The final pipeline chains all three steps together

---

## Run the Examples

```bash
python tutorial/easy/step1_simple_llm_calls/step1_simple_llm.py
python tutorial/easy/step1_simple_llm_calls/step2_pipe_sequence.py
python tutorial/easy/step1_simple_llm_calls/step3_pipe_compose.py
```

---

## Summary

| Pipe Type | Purpose |
|-----------|---------|
| `PipeLLM` | Make LLM calls to generate or transform text |
| `PipeSequence` | Chain multiple pipes together in sequence |
| `PipeCompose` | Create formatted output using templates |

**Next:** Learn how to work with [Structured Objects](../step2_structured_objects/)!
