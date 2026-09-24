# Key: capybara_for_kids

Inputs: `user_prompt`, inline in `inputs.json`, a structured request for a long, casual blog article about capybaras written for children. It is the request the example has always shipped with.

## Planted facts
F1. The topic is "Capybara".
F2. The audience is "Kids".
F3. The tone is "Casual".
F4. The length is "Long", which the method sets at about 2,000 words, in sections of 250 to 300 words.
F5. The free-form instruction asks for "a fun and engaging blog article".

## Must
M1. `seo_title` is filled, names capybaras, and is at most 60 characters long.
M2. `meta_description` is filled, names capybaras, and is at most 160 characters long.
M3. `content` is Markdown opening with one level-1 heading, followed by at least five level-2 sections.
M4. `content` runs to at least 1,500 words.
M5. `content` is about capybaras from start to finish.
M6. `content` is written for children: plain words and short sentences, with any technical term (such as "rodent" or "semi-aquatic") explained where it appears.
M7. `content` is casual and playful: it speaks to the reader as "you", uses contractions, and reads as fun rather than as a report.
M8. `content` gives at least three concrete, accurate facts about capybaras, such as that they are the largest rodents alive, that they come from South America, that they are good swimmers, that they eat grass and water plants, or that they live in groups.

## Must not
N1. A plain factual error about capybaras: that they are not rodents, that they eat meat, that they are native outside Central and South America, or that they are dangerous predators.
N2. Violent, frightening or otherwise unsuitable detail for children.
N3. SEO scaffolding left in `content`: a "Meta description" or "SEO title" line, a keyword list, or a placeholder such as "[Insert image]".
N4. `content` wrapped in a Markdown code fence.
N5. An academic or corporate register in `content`: unexplained jargon, citations, or a references section.

## Also acceptable
A1. A level-1 heading in `content` that repeats `seo_title` or gives a friendlier variant of it, for M3.
A2. A section written as a list of fun facts, a quiz or a short activity for children, for M3 and M8.

## Pass bar
Every Must and Must not line.
