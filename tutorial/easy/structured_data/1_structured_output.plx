domain = "structured_output"
description = "Get structured data from LLMs"

[concept]

# Define the structure of a book idea
[concept.BookIdea]
description = "A book idea with title, genre, and synopsis"

[concept.BookIdea.structure]
title = { type = "text", description = "The book title", required = true }
genre = { type = "text", description = "The genre of the book", required = true }
synopsis = { type = "text", description = "A brief synopsis of the book" }
target_audience = { type = "text", description = "Who this book is for" }

[pipe]

# Generate a structured book idea
[pipe.struct_generate_book_idea]
type = "PipeLLM"
description = "Generate a structured book idea"
output = "BookIdea"
prompt = """
Generate a creative book idea. Provide a compelling title, genre, synopsis, and target audience.
"""
