domain = "retrieve"
description = "The domain for retrieving relevant excerpts from text"

[concept]
RetrievedExcerpt = "An excerpt from a text with its justification for being relevant to a question"

[pipe]
[pipe.retrieve_excerpts]
type = "PipeLLM"
description = "Find the most relevant excerpt in a text that answers a specific question"
inputs = { text = "Text", question = "answer.Question" }
output = "RetrievedExcerpt[]"
model = "llm_to_retrieve"
prompt = """
Your task is to find all relevant excerpts from a text that contribute to answering a question.
It might not contain the exact answer, but it should be relevant to the question.

@text

@question

Justify why you chose those excerpts. Do not modify the original text.
"""

