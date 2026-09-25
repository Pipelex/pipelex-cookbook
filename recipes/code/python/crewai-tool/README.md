# A method as a CrewAI agent's tool

An agent framework is good at deciding what to do next and poor at doing one thing the same way every time. This recipe gives a CrewAI crew a Pipelex method as a tool, so the part that must be repeatable comes out of a fixed pipeline with a typed result, and the crew keeps its freedom around it.

The crew has two agents:

- **The analyst** calls `draft_research_brief`, a CrewAI tool that runs the cookbook's [research report](../../../../methods/research_report/) method by its address and returns the brief as JSON: an executive summary, key findings and open questions, validated by the `ResearchBrief` model generated from the method.
- **The editor** turns the brief into a one-page memo for a decision-maker. The method drafts from its model's own knowledge and searches no source, so the editor lists the claims to verify before anyone relies on them.

## What it needs

- [uv](https://docs.astral.sh/uv/), which reads the script's dependencies from its first lines and installs them, including CrewAI.
- A Pipelex API key in `PIPELEX_API_KEY`, from [app.pipelex.com](https://app.pipelex.com). The tool's call is one run on the hosted API and spends credit.
- A model for the crew's own agents. CrewAI uses OpenAI unless told otherwise, so set `OPENAI_API_KEY`, or set `MODEL` and that provider's key as [CrewAI's documentation](https://docs.crewai.com/en/concepts/llms) describes.

## Run it

```bash
export PIPELEX_API_KEY=… OPENAI_API_KEY=…
uv run crew.py "What are the tradeoffs of LFP versus NMC batteries for grid storage?"
```

## What you get

The memo, printed and saved to `memo.md`: a short answer, the findings that matter for a decision, what remains open, and the claims to verify in sources. The brief the analyst worked from comes from one run, whose id the tool prints on the terminal.

## How it is built

- `crew.py` calls the method by its address, `github.com/Pipelex/pipelex-cookbook/research_report@v0.18.0`, pinned to a release tag so the method never changes under the types. It runs the pipe `research_report.deep_research`, which returns the typed brief, rather than the package's main pipe, which renders it as Markdown.
- `generated/research_report/` holds the method's types: `models.py`, generated from the method at that tag, and `codegen.lock`, which vouches for it. `sources.json` records the address and the target they come from. Never edit them by hand: in the cookbook, `make refresh` regenerates them, and in your own project `/pipelex-integrate` does.
- The tool is an ordinary `BaseTool` whose `_run` waits for the run, so any other framework that takes a Python function as a tool takes the same `draft_brief` coroutine.
