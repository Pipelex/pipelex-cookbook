domain = "answer"
description = "The domain for questions and answers"

[concept]
Answer = "An answer to a question"
Question = "A question to a problem"
EnrichedQuestion = "An enriched question"

[pipe]
[pipe.retrieve_then_answer]
type = "PipeSequence"
description = "Answer a question, given the target type and the excerpts neeeded to answer it"
inputs = { question = "answer.Question", text = "Text", client_instructions = "Text" }
output = "Dynamic"
steps = [
  { pipe = "write_context_of_text", result = "context" },
  { pipe = "retrieve_excerpts", result = "excerpts" },
  { pipe = "enrich_question", result = "enriched_question" },
  { pipe = "answer_question", result = "answer" },
]

[pipe.answer_question]
type = "PipeSequence"
description = "Answer the question in a dynamically specified format"
inputs = { enriched_question = "EnrichedQuestion", client_instructions = "Text", context = "Text", excerpts = "retrieve.RetrievedExcerpt" }
output = "Dynamic"
steps = [
  { pipe = "pre_answer_question", result = "answer" },
  { pipe = "cleanse_answer", result = "cleaned_answer" },
]

[pipe.write_context_of_text]
type = "PipeLLM"
description = "Write the context of a sample of text"
inputs = { text = "Text" }
output = "Text"
prompt = """
Your task is to write the context of a text.
This context should be maximum of 30 words.
The goal is to quickly understand the type of ducument by just reding this context.

@text
"""

[pipe.enrich_question]
type = "PipeLLM"
description = "Get an enriched question"
inputs = { question = "answer.Question", client_instructions = "Text", context = "Text" }
output = "EnrichedQuestion"
model = "llm_to_enrich"
prompt = """
Your task is to reformulate a form field or a question into a question for a LLM.
This question will need an answer from a text.

@context

Here is the question/field name: '$question'.
Each word is important therefore do not extrapolate or create information.

{% if client_instructions %}
Here are important instructions from the customer to take into account in order to enrich the question.
The client instructions are important and you absolutely must follow them. However, it DOES NOT contain the answer.
@client_instructions
{% endif %}

Here is the main task: If I were to prompt an LLM to extract this information from a specific section of the contract, what should I ask?

Here are some rules that you absolutely must follow:
- No need to add instructions like "based on the provided contract", just write the question in English, no need for code.
- No need for intros like "Here is a reformulated question", just write the question.
- It is important that you specify that the question is a Yes/No question if it is the case.
"""

[pipe.pre_answer_question]
type = "PipeLLM"
description = "Answer the question in a dynamically specified format"
inputs = { enriched_question = "EnrichedQuestion", excerpts = "retrieve.RetrievedExcerpt", context = "Text", client_instructions = "Text" }
output = "Dynamic"
model = "llm_to_answer"
structuring_method = "preliminary_text"
prompt = """
Your task is to answer a question based on excerpts previously retrieved from a text.
To help you, your assistant has already enriched the question and extracted the most relevant excerpts{% if client_instructions %},
and provided you with some hints or guidelines from the customer{% endif %}.

@context

@enriched_question

@excerpts
Not all of of the exceprts are necessarily relevant to the question, but all of them are relevant to the contract.

{% if client_instructions %}
Here are important instructions from the customer to take into account in order to enrich the question.
The client instructions are important and you absolutely must follow them. However, it DOES NOT contain the answer.
@client_instructions
{% endif %}

Important rules for answering:
- For Yes/No questions: Answer "NO" if no excerpts or inconclusive evidence (with explanation) are provided.
- For multiple choice questions: Mark as "indeterminate" if no excerpts or inconclusive evidence (with explanation) are provided.
- Always cite the answer with citations EXCEPT when the answer is "indeterminate"
- When evidence is clear: Provide answer with citations
- When no answer is applicable, or the answer says that its not applicable, mark as "not_applicable" with explanation.
- If the target_format is FreeText, it must be a text.
- [IMPORTANT] DO NOT add commentaries like "Based on.. According to...", just output the answer.
- [IMPORTANT] DO NOT extrapolate or create information. Base your answer solely on the provided excerpts.
- Please, cite the exact sentences that you used to answer the question in a "citation" paragraph.
- Make sure that you also cite the clause number if provided (20.1 for instance).

Here is the fields format of the answer you must output:
"""

[pipe.cleanse_answer]
type = "PipeLLM"
description = "Clean the answer"
inputs = { answer = "Dynamic" }
output = "Dynamic"
structuring_method = "preliminary_text"
prompt = """
You are helping to clean answers that were generated from analyzing document excerpts to answer specific questions.

@answer

Your task is to clean the answer by handling cases where no clear answer could be found in the document excerpts.

ONLY output the cleaned answer - do not add any explanation or commentary.

If the answer contains any of these patterns, output "Indeterminate":
- Empty or blank answers (including empty JSON objects)
- Statements indicating no relevant information was found
- Phrases like:
  * "The excerpts are not relevant to the question"
  * "There is nothing relevant in the document to answer"
  * "Based on the document, there is nothing..."
  * "No information found in the document"
  * "Cannot determine from the provided excerpts"
  * "No relevant excerpts were found"

Important rules:
- Keep "NO" answers unchanged
- Keep "not_applicable" or "indeterminate" answers unchanged
- Preserve all other valid answers exactly as they are
- DO NOT add any explanation or commentary to your output
"""

