domain = "document_qa"
description = "Extract text from documents and answer questions"
main_pipe = "document_qa"

[concept]

# Define the structure of an answer
[concept.Answer]
description = "An answer to a question about a document"

[concept.Answer.structure]
answer = { type = "text", description = "The answer to the question", required = true }
confidence = { type = "text", description = "How confident: high, medium, or low" }
source_quote = { type = "text", description = "A quote from the document that supports the answer" }

[pipe]

# First pipe: Extract text from a PDF document
[pipe.extract_text]
type = "PipeExtract"
description = "Extract text from a PDF document"
inputs = { document = "Document" }
output = "Page[]"

# Second pipe: Answer a question based on the extracted text
[pipe.answer_question]
type = "PipeLLM"
description = "Answer a question about the document"
inputs = { pages = "Page[]", question = "Text" }
output = "Answer"
prompt = """
Based on the following document content, answer the question.

Document:
@pages

Question: $question

Provide a clear answer, your confidence level, and a supporting quote from the document.
"""

# Full pipeline: Extract text and answer question
[pipe.document_qa]
type = "PipeSequence"
description = "Extract text from a document and answer a question"
inputs = { document = "Document", question = "Text" }
output = "Answer"
steps = [
    { pipe = "extract_text", result = "pages" },
    { pipe = "answer_question", result = "answer" },
]
