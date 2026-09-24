# Key: fintech_article

Inputs: `assets/extract_generic/fintech_article_with_text_in_images.pdf`, a two-page article about QuantumFlex, a fictional quantum-computing fintech platform by the startup NexaCore, whose first page ends with a diagram of three circles and whose second page is set in two columns. It is the sample the example has always shipped with.

## Planted facts
F1. Page 1 opens with the title "QuantumFlex: Revolutionizing the Financial Technology Landscape", then the sections Introduction, The Technology Behind QuantumFlex and Market applications.
F2. The Introduction says the Boston-based startup NexaCore launched QuantumFlex after three years in stealth and has secured $87 million in Series B funding led by Vertex Ventures and Sequoia Capital. The next section names the "Neural Quantum Mesh" (NQM) architecture and quotes Dr. Amara Chen, NexaCore's Chief Technology Officer.
F3. Market applications is a picture of three circles whose text is absent from the PDF's text layer: RiskSphere, "A quantum-enhanced risk assessment tool that dynamically evaluates portfolio" (cut short as printed); MarketPulse, "A predictive analytics engine that forecasts market movements by analyzing quantum correlations"; AlphaQuant, "An investment strategy optimizer that automatically rebalances portfolios based on quantum probability distributions."
F4. Page 2 is set in two columns followed by a full-width Conclusion. The left column holds Industry Response and the start of Future Developments, which breaks mid-quote after "Within eighteen months, we intend to bring"; the right column resumes with "quantum-enhanced financial planning to individual consumers through partnerships with major retail banks.", then the paragraph on a cloud-based API, then Challenges and Concerns.
F5. Page 2 names Marcus Blakely, a financial technology analyst at Goldman Sachs; the Financial Technology Association's planned Quantum Finance Working Group; CEO Vanessa Rodriguez and the plan to reach retail banking by Q3 2024; the SEC; and Dr. Jason Mendoza of the CyberDefend Institute.

## Must
M1. The output is a list of two texts, one per page, the first page's first.
M2. The first page's `text` opens with the title "QuantumFlex: Revolutionizing the Financial Technology Landscape" as a heading, followed by headings for Introduction, The Technology Behind QuantumFlex and Market applications.
M3. The first page's `text` says the Boston-based startup NexaCore secured $87 million in Series B funding led by Vertex Ventures and Sequoia Capital.
M4. The first page's `text` names the Neural Quantum Mesh (NQM) architecture and Dr. Amara Chen as NexaCore's Chief Technology Officer.
M5. The first page's `text` gives, under Market applications, the three applications drawn in the circles, each with its description: RiskSphere, a quantum-enhanced risk assessment tool that dynamically evaluates portfolios; MarketPulse, a predictive analytics engine that forecasts market movements by analyzing quantum correlations; AlphaQuant, an investment strategy optimizer that automatically rebalances portfolios based on quantum probability distributions.
M6. The second page's `text` has headings for Industry Response, Future Developments, Challenges and Concerns and Conclusion, in that order.
M7. The second page's `text` gives Vanessa Rodriguez's quote as one continuous passage under Future Developments, running from "Our vision extends beyond institutional finance" to "through partnerships with major retail banks."
M8. The second page's `text` keeps the paragraph on a cloud-based API for third-party developers under Future Developments, before Challenges and Concerns.
M9. The second page's `text` names Marcus Blakely of Goldman Sachs, the Quantum Finance Working Group, the SEC and Dr. Jason Mendoza of the CyberDefend Institute.

## Must not
N1. Lines of the two columns of the second page interleaved, a left-column line followed by the right-column line beside it, such as "describes QuantumFlex as based API that would allow third-party".
N2. A figure or name that differs from the page's, such as $87 billion, a Series A round, or retail banking by Q3 2025.
N3. A text wrapped in a code fence such as "```markdown", or opened by a sentence about the task such as "Here is the markdown".
N4. Content of one page repeated in the other page's text.
N5. A fourth market application, or an application described with a claim its circle does not make.

## Also acceptable
A1. The three applications set as a table, a list or three headed paragraphs, for M5.
A2. RiskSphere's description ending "evaluates portfolio", as printed, or "evaluates portfolios", for M5.
A3. Any heading levels, as long as the headings are Markdown headings, for M2 and M6.

## Pass bar
Every Must and Must not line.
