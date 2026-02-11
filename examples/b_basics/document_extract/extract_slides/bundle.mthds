domain = "extract_slides"
description = "The domain of extracting slides from documents"
main_pipe = "extract_slides"

[concept]
[concept.Slide]
description = "A slide from a presentation"
[concept.Slide.structure]
title = { type = "text", description = "The title of the slide" }
text_markdown = { type = "text", description = "The content of the slide as markdown" }
description = { type = "text", description = "A description of the slide: layout of the text, description of the graphics" }

[pipe]

[pipe.extract_slides]
type = "PipeSequence"
description = "Extract markdown from a document"
inputs = { document = "Document" }
output = "Text"
steps = [
    { pipe = "extract_markdown_and_views_from_document", result = "pages" },
    { pipe = "describe_slide", batch_over = "pages", batch_as = "page", result = "slides" },
    { pipe = "concatenate_slide_descriptions", result = "slides_description" },
]

[pipe.extract_markdown_and_views_from_document]
type = "PipeExtract"
description = "Extract page text markdown and views from a document"
inputs = { document = "Document" }
output = "Page[]"
page_views = true
model = "azure-document-intelligence"


[pipe.describe_slide]
type = "PipeLLM"
description = "Describe a slide"
inputs = { page = "Page" }
output = "Slide"
model = "gemini-3.0-pro"
system_prompt = """
You are a professional presentation designer. You excel in describing slides with the details that matter.
"""
prompt = """
Describe this slide:
{{ page.text_and_images.text | tag("extracted_text") }}

Rendered slide: $page.page_view

- Devise the slide's title.
- Copy (and if required cleanup) the extracted text, except the title and html comments like `<!-- PageHeader="Use-Cases" -->` ifthere are any.
- Complete with the description of the slide: layout of the text, description of the graphics.
"""

[pipe.concatenate_slide_descriptions]
type = "PipeCompose"
description = "Concatenate slide descriptions"
inputs = { slides = "Slide[]" }
output = "Text"
template = """
{% for slide in slides %}
# {{ slide.title }}

$slide.text_markdown

> **Description:**
$slide.description
{% endfor %}

---

"""