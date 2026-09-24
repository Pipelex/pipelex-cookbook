# Key: student_profiles

Inputs: `data_description`, the Markdown template of a student profile the example has always shipped with, and `nb_samples`, 5. The template is a form with bracketed blanks: a name, a performance level, three learning-style choices, three free-text background fields, hobbies, career goals and two preference choices.

## Planted facts
F1. `nb_samples` asks for five samples.
F2. The template fixes the options of six fields: Current Performance is Struggling, Average or Advanced; Learns Best With is Visual examples, Step-by-step text, Hands-on practice or Videos; Pace is Needs more time, Normal or Fast learner; Complexity is Prefers simple explanations, Balanced or Likes deep details; Example Style is Many real-world examples, Abstract concepts or Mix; Question Format is Multiple choice, Short answer or Open discussion.
F3. The other six fields are free text: the student's name, Strengths, Needs Help With, Prior Knowledge, Hobbies/Interests and Career Goals, the last one allowing "undecided".
F4. The method first plans the cases to cover, then fills one profile per case, so the samples are meant to differ from one another, edge cases included.

## Must
M1. The output is a list of exactly five samples.
M2. Every sample fills all twelve fields with a non-empty value: `student_name`, `current_performance`, `learns_best_with`, `pace`, `complexity`, `strengths`, `needs_help_with`, `prior_knowledge`, `hobbies_interests`, `career_goals`, `example_style` and `question_format`.
M3. Every choice field holds exactly one of the template's options: `current_performance` is Struggling, Average or Advanced; `learns_best_with` is Visual examples, Step-by-step text, Hands-on practice or Videos; `pace` is Needs more time, Normal or Fast learner; `complexity` is Prefers simple explanations, Balanced or Likes deep details; `example_style` is Many real-world examples, Abstract concepts or Mix; `question_format` is Multiple choice, Short answer or Open discussion.
M4. The five `student_name` values are five different names.
M5. Across the five samples, `current_performance` takes at least two different values, and so does `pace`.
M6. Each sample reads as one coherent student: its `strengths`, `needs_help_with` and `prior_knowledge` are about school subjects or skills, and its `hobbies_interests` and `career_goals` name actual interests and goals (or "undecided" for career goals), in any wording.

## Must not
N1. A field left as the template's placeholder, such as "[Student Name]", "[subjects or topics they're good at]" or "e.g., soccer, video games, music".
N2. A choice field holding a value outside its options, or two options joined ("Visual examples / Videos").
N3. Two samples identical in all six choice fields and in `strengths` and `needs_help_with`, which would be the same student under two names.

## Also acceptable
A1. `career_goals` given as "Undecided", or as "Undecided, curious about …", for M2 and M6.
A2. A free-text field written as a comma-separated list rather than a sentence, for M2 and M6.

## Pass bar
Every Must and Must not line.
