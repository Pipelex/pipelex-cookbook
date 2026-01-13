domain = "tables"
description = "Extracting tables from images"
system_prompt = "You are an expert at data tables and html syntax and you have a strong attention to details."

[concept]
HtmlTable = "An HTML table"

[concept.TableScreenshot]
description = "A screenshot of a table (table in the sense of a data structure used to organize information in rows and columns)"
refines = "Image"

[pipe]
[pipe.extract_html_table_from_image]
type = "PipeLLM"
description = "Get an HTML table"
inputs = { table_screenshot = "TableScreenshot" }
output = "HtmlTable"
model = "llm_for_table_to_text"
model_to_structure = "llm_for_table_to_text"
prompt = """
You are given an image which is a view of a table, taken from a document: $table_screenshot.
Your goal is to extract the table from the image **in html**.

Make sure you do not forget any text.
Make sure you do not invent any text.
Make sure your merge is consistent.
Make sure you replicate the formatting (borders, text formatting, colors, text alignement...)
"""

[pipe.review_html_table]
type = "PipeLLM"
description = "Review an HTML table"
inputs = { table_screenshot = "TableScreenshot", html_table = "HtmlTable" }
output = "HtmlTable"
model = "llm_for_table_to_text"
model_to_structure = "llm_for_table_to_text"
prompt = """
Your role is to correct an html_table to make sure that it matches the one in the provided image: $table_screenshot.

@html_table

Pay attention to the text and formatting (color, borders, ...).
Rewrite the entire html table with your potential corrections.
Make sure you do not forget any text.
"""


[pipe.extract_html_table_and_review]
type = "PipeSequence"
description = "Get an HTML table and review it"
inputs = { table_screenshot = "TableScreenshot" }
output = "HtmlTable"
steps = [
    { pipe = "extract_html_table_from_image", result = "html_table" },
    { pipe = "review_html_table", result = "reviewed_html_table" },
]

