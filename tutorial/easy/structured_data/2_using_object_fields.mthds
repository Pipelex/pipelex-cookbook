domain = "using_object_fields"
description = "Use specific fields from structured objects"
main_pipe = "generate_and_pitch"

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

# First pipe: Generate a structured book idea
[pipe.fields_generate_book_idea]
type = "PipeLLM"
description = "Generate a structured book idea"
output = "BookIdea"
prompt = """
Generate a creative book idea. Provide a compelling title, genre, synopsis, and target audience.
"""

# Second pipe: Use only title and genre to write a pitch
[pipe.write_pitch]
type = "PipeLLM"
description = "Write a marketing pitch using only title and genre"
inputs = { book_idea = "BookIdea" }
output = "Text"
prompt = """
Write a compelling one-paragraph marketing pitch for this book:

Title: $book_idea.title
Genre: $book_idea.genre

Focus on why readers of this genre would love this book.
"""

# Full pipeline: Generate book idea and write pitch
[pipe.generate_and_pitch]
type = "PipeSequence"
description = "Generate a book idea then write a marketing pitch"
output = "Text"
steps = [
    { pipe = "fields_generate_book_idea", result = "book_idea" },
    { pipe = "write_pitch", result = "marketing_pitch" },
]
