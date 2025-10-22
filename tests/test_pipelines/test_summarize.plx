

domain = "test_summarize"
description = "Example of summarizing text by topics."
system_prompt = "You are an expert at summarizing text."

[concept] ####### Concept definitions ############################
Topic = "A topic a text deals with."
Summary = "A concise rewriting of a dense text."

[pipe] ####### Pipe definitions ##################################

[pipe.test_summarize_with_structure]
type = "PipeLLM"
description = "Summarize text."
inputs = { text = "Text" }
output = "StructuredSummary"
prompt = """
You are given a text.
Your task is to summarize it accurately.

@text

Please provide only the summary, with no additional text or explanations.
"""

[pipe.test_summarize_by_steps]
type = "PipeSequence"
description = "Summarize text by steps: extract topics, summarize for each topic, summarize from summaries."
inputs = { text = "Text" }
output = "Summary"
steps = [
    { pipe = "test_extract_topics", result = "topics" },
    { pipe = "test_summarize_topic", batch_over = "topics", batch_as = "topic", result = "summarized_topics" },
    { pipe = "test_summarize_from_summaries", result = "summary" },
]

[pipe.test_extract_topics]
type = "PipeLLM"
description = "Extract the topics from a dense text."
inputs = { text = "Text" }
output = "Topic[]"
prompt = """
You are given a large text.
Your task is to extract the main topics from the text.
@text
Please provide only the main topics, with no additional text or explanations.
"""


[pipe.test_summarize_topic]
type = "PipeLLM"
description = "Summarize a dense text with of focus on a specific topic."
inputs = { text = "Text", topic = "Topic" }
output = "Summary"
prompt = """
Your goal is to summarize everything related to $topic in the provided text:

@text

Please provide only the summary, with no additional text or explanations.
Your summary should not be longer than 2 sentences.
"""

[pipe.test_summarize_from_summaries]
type = "PipeLLM"
description = "Summarize text from summarized topics."
inputs = { summarized_topics = "Summary" }
output = "Summary"
prompt = """
You are given a list of summaries that cover different topics from a large text.

Your task is to generate an overall summary of the text based on the provided summaries, avoiding any repetitions.

@summarized_topics

Please provide only the summary, with no additional text or explanations.
"""

