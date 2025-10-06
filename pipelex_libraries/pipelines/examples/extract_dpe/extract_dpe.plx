domain = "power_extractor"
description = "The domain for power extractor"

[concept]
Dpe = "A diagnostic of the energy performance of a building"

[pipe]
[pipe.power_extractor_dpe]
type = "PipeSequence"
description = "Update page content with markdown"
inputs = { document = "PDF" }
output = "Dpe"
steps = [
    { pipe = "ocr_page_contents_and_views_from_pdf", result = "page_contents" },                                                # Located in the base library, in the domain "documents"
    { pipe = "write_markdown_from_page_content_dpe", batch_over = "page_contents", batch_as = "page_content", result = "dpe" },
]

[pipe.write_markdown_from_page_content_dpe]
type = "PipeLLM"
description = "Write markdown from page content of a 'Diagnostic de Performance Energetique'"
inputs = { "page_content.page_view" = "Image", page_content = "Page" }
output = "Dpe"
llm = "llm_for_img_to_text"
structuring_method = "preliminary_text"
system_prompt = """You are a multimodal LLM, expert at converting images into perfect markdown."""
prompt_template = """
You are given an image of a French 'Diagnostic de Performance Energetique'.
Your role is to convert the image into perfect markdown.

To help you do so, you are given the text extracted from the page by an OCR model.
@page_content.text_and_images.text.text

- It is very important that you collect every element, especially if they are related to the energy performance of the building.
- Pay attention to all the pieces of information that may be included in images, graphs, charts, or tables.
- We value letters like "A, B, C, D, E, F, G" as they are energy performance classes.
- Pay attention to the text alignment, it might have been misaligned by the OCR.
- The OCR extraction may be highly incomplete. It is your job to complete the text and add the missing information using the image.
- Output only the markdown, nothing else. No need for "```markdown" or "```".
- You can use HTML if it helps you.
- You can use tables if it is relevant.
"""

