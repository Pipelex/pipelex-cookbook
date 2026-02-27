# Structured Data

Learn how to get structured objects from LLMs and extract text from documents.

---

## 1. Structured Output

Instead of plain text, get a **structured object** with specific fields.

**File: `1_structured_output.mthds`**

```plx
domain = "structured_output"
description = "Get structured data from LLMs"
main_pipe = "struct_generate_book_idea"

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
```

**What you need to know:**
- `[concept.BookIdea]` - Define a new type of structured data
- `[concept.BookIdea.structure]` - Define the fields it has
- `output = "BookIdea"` - The LLM returns this structured object

**Run it:**
```bash
pipelex run pipe tutorial/easy/structured_data/1_structured_output.mthds
```

---

## 2. Using Object Fields

Access **specific fields** from a structured object in your prompts.

**File: `2_using_object_fields.mthds`**

```plx
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
```

**What you need to know:**
- `$book_idea.title` - Access the `title` field from the `book_idea` object
- You can pick just the fields you need

**Run it:**
```bash
pipelex run pipe tutorial/easy/structured_data/2_using_object_fields.mthds
```

---

## 3. Document Q&A

Extract text from a **PDF** and answer questions about it.

**File: `3_document_qa.mthds`**

```plx
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
```

**What you need to know:**
- `PipeExtract` - Extracts text from PDFs or images using OCR
- `Document` - A built-in type for PDF files
- `Page[]` - A list of pages extracted from the document

**inputs.json:**

For native types like `Document`, you need to wrap the content with a `concept` key:

```json
{
  "document": {
    "concept": "native.Document",
    "content": {
      "url": "assets/simple_ocr/illustrated_train_article.pdf"
    }
  },
  "question": "What is the main topic of this document?"
}
```

> **Note:** Simple text inputs can be passed directly (like `"question": "..."`), but native types like `Document` and `Image` require the `concept` wrapper format.

**Run it:**
```bash
pipelex run bundle tutorial/easy/structured_data/3_document_qa.mthds -i tutorial/easy/structured_data/inputs.json
```

---

## Summary

| Concept | What it does |
|---------|--------------|
| `[concept.X.structure]` | Define a structured data type with fields |
| `$obj.field` | Access a specific field from an object |
| `PipeExtract` | Extract text from PDFs and images |

**Congratulations!** You've completed the easy tutorials. You now know how to:
- Make LLM calls and chain them together
- Get structured data from LLMs
- Extract and process documents

**Next:** Learn about [Model Configuration, Batch Processing, and Parallel Execution](../../medium/)!
