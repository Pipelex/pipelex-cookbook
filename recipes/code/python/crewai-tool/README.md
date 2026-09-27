# A method as a CrewAI agent's tool

An agent framework is good at deciding what to do next and poor at doing one thing the same way every time. This recipe gives a CrewAI crew a Pipelex method as a tool, so the part that must be repeatable comes out of a fixed pipeline with a typed result, and the crew keeps its freedom around it.

The crew has two agents:

- **The reviewer** calls `review_nda`, a CrewAI tool that runs the cookbook's [NDA review](https://github.com/Pipelex/pipelex-cookbook/tree/v0.20.0/methods/review_nda) method by its address on a counterparty's NDA, against the company's NDA playbook, and returns the review as JSON: a verdict, a note for counsel, and one row per position of the playbook with the clause found, the assessment and the playbook's fallback wording, validated by the `NdaReview` model generated from the method. The playbook is the company's and does not change from one NDA to the next, so the tool holds it, and the agent names only the NDA.
- **The editor** turns the review into a one-page memo for the colleague who needs the NDA signed: whether it can be signed now, what to ask for instead, and what goes to counsel. It is told to add no legal judgment of its own.

## What it needs

- [uv](https://docs.astral.sh/uv/), which reads the script's dependencies from its first lines and installs them, including CrewAI.
- A Pipelex API key in `PIPELEX_API_KEY`, from [app.pipelex.com](https://app.pipelex.com). The tool's call is one run on the hosted API and spends credit.
- A model for the crew's own agents. CrewAI uses OpenAI unless told otherwise, so set `OPENAI_API_KEY`, or set `MODEL` and that provider's key as [CrewAI's documentation](https://docs.crewai.com/en/concepts/llms) describes.

## Run it

```bash
export PIPELEX_API_KEY=… OPENAI_API_KEY=…
uv run crew.py
```

With no argument, the crew reviews the method's sample: Common Paper's Mutual NDA, its cover page completed for the example as a counterparty's draft, against a playbook written for the example. For your own NDA, give its link, which the hosted API must be able to fetch, and your playbook as a text or Markdown file:

```bash
uv run crew.py https://example.com/their-nda.pdf --playbook our-nda-playbook.md
```

## What you get

The memo, printed and saved to `memo.md`. The review the reviewer worked from comes from one run, whose id the tool prints on the terminal.

On the sample NDA, the review's verdict was `Escalate to counsel`: the cover page adds a non-solicitation clause, which the playbook refuses in an NDA, and the confidentiality period, set to last in perpetuity, is one to negotiate down to the playbook's five years. The memo said the NDA cannot be signed as it stands, set out every position of the playbook in a table with the wording to propose for those two, and sent both to counsel with the reason for each. The editor runs on CrewAI's model and wrote the confidentiality period's wording in its own words, where the review quotes the playbook's exactly: that is the line this recipe draws, between the crew's freedom and the method's fixed, typed result.

## How it is built

- `crew.py` calls the method by its address, `github.com/Pipelex/pipelex-cookbook/review_nda@v0.20.0`, pinned to a release tag so the method never changes under the types. It gives the NDA as a document by its link, and the playbook as the method's `NdaPlaybook`; with no `--playbook`, it reads the sample playbook from the method's `inputs.json` at that release.
- `generated/review_nda/` holds the method's types: `models.py`, generated from the method at that tag, and `codegen.lock`, which vouches for it. `sources.json` records the address and the target they come from. Never edit them by hand: in the cookbook, `make refresh` regenerates them, and in your own project `/pipelex-integrate` does.
- The tool is an ordinary `BaseTool` whose `_run` waits for the run, so any other framework that takes a Python function as a tool takes the same `review_nda` coroutine.
