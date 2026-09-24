# CrewAI with Pipelex as a Typed Tool

## What's happening here

**Pipelex is a tool for AI agents.** It lets you define repeatable, typed LLM workflows in `.mthds` files — and any agent (CrewAI, LangGraph, custom) can call them as a single function. Think of it as a stored procedure for LLMs: define the steps once, get the same structured output every time. No prompt drift, no missing fields, no format surprises.

**CrewAI is the agent orchestration layer.** It decides *when* to call the Pipelex tool, passes results between agents, and handles side effects (saving files, sending emails, hitting APIs) — things Pipelex intentionally doesn't do.

```
Pipelex                                        CrewAI
"What to compute and how to format it"         "When to run it and what to do with the result"

- Validated inputs/outputs (Pydantic)           - Agent decides to call the tool
- Typed LLM calls (PipeLLM)                     - Passes result to next agent
- Batch fan-out (PipeBatch)                     - Side effects: save file, send email
- Deterministic templates (PipeCompose)         - Could loop, retry, branch (agent reasoning)
- Same structure every run
```

Pipelex replaces the part of agent workflows where you need **reliability** — structured extraction, fact-checking, templated output. CrewAI handles the part that needs **flexibility** — deciding what to do next, interacting with external systems. Neither replaces the other.

## The method

The pipes come from the cookbook's [`research_report`](../../../methods/research_report/) method, which anyone can also run by address on the hosted Pipelex API. Its main pipe, `prepare_report`, is a single `PipeSequence` that chains:

- `gather_sources` (PipeLLM) → 3 typed `SourceSummary`s
- `verify_claim` (PipeBatch) → batch fact-check each summary → `FactCheck`s
- `synthesize_brief` (PipeLLM) → typed `ResearchBrief`
- `compose_report` (PipeCompose) → deterministic markdown report (same structure every run)

## The crew

The crew splits that chain between two agents:

1. **Researcher** (Pipelex-backed) — its `run_research` tool calls `deep_research`, the first three steps, and returns the typed `ResearchBrief`'s fields.
2. **Publisher** (Pipelex + vanilla CrewAI) — its `compose_report` tool renders the brief through the `compose_report` pipe, then `save_report` writes a `.md` file and `send_email` writes to `outbox.txt`. Side effects Pipelex intentionally doesn't do.

| Layer | Responsibility | Pipes used |
|---|---|---|
| Pipelex `PipeLLM` | LLM extraction + fact-checking | gather, verify, synthesize |
| Pipelex `PipeBatch` | Fan-out over a list | verify each summary |
| Pipelex `PipeCompose` | Deterministic Jinja template (no LLM) | compose_report |
| CrewAI | Agent reasoning + side effects | save_report, send_email |

## Flow to build one of these

1. Author the bundle: `/mthds-build`, `/mthds-check`.
2. Declare each typed output as a concept with a structure in the bundle, as `ResearchBrief` is: Pipelex validates every output against it, with no Python class to generate or keep in sync.
3. Wrap the pipe in a `@tool` function. Drop it into a crew with other agents.

## Files

- [`methods/research_report/bundle.mthds`](../../../methods/research_report/bundle.mthds) — full bundle, with the `ResearchBrief` concept
- `run_crew_with_pipelex.py` — two-agent sequential crew, which loads the bundle from `methods/research_report/`

## Install + run

```bash
uv pip install -e ".[crewai]"
uv run python examples/c_advanced/crewai_with_pipelex_tools/run_crew_with_pipelex.py
```

Requires two API keys in `.env`:

- `PIPELEX_GATEWAY_API_KEY` — drives the Pipelex pipeline (`pipelex login` to get one)
- `OPENAI_API_KEY` — drives the CrewAI agent reasoning

After the run, check `reports/report.md` and `outbox.txt` in this directory.
