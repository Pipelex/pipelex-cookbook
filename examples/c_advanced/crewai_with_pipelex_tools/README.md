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

## The crew

1. **Report Creator** (Pipelex-backed) — calls `prepare_report`, a single `PipeSequence` that chains:
   - `gather_sources` (PipeLLM) → 3 typed `SourceSummary`s
   - `verify_claim` (PipeBatch) → batch fact-check each summary → `FactCheck`s
   - `synthesize_brief` (PipeLLM) → typed `ResearchBrief`
   - `compose_report` (PipeCompose) → deterministic markdown report (same structure every run)
2. **Publisher** (vanilla CrewAI) — `save_report` writes a `.md` file, `send_email` writes to `outbox.txt`. Side effects Pipelex intentionally doesn't do.

| Layer | Responsibility | Pipes used |
|---|---|---|
| Pipelex `PipeLLM` | LLM extraction + fact-checking | gather, verify, synthesize |
| Pipelex `PipeBatch` | Fan-out over a list | verify each summary |
| Pipelex `PipeCompose` | Deterministic Jinja template (no LLM) | compose_report |
| CrewAI | Agent reasoning + side effects | save_report, send_email |

## Flow to build one of these

1. Author the bundle: `/mthds-build`, `/mthds-check`.
2. Generate Pydantic structures: `pipelex build structures research_report.mthds`.
3. Wrap the pipe in a `@tool` function. Drop it into a crew with other agents.

## Files

- `research_report.mthds` — full bundle
- `structures/research_report__research_brief.py` — Pydantic `ResearchBrief(StructuredContent)`
- `run_crew_with_pipelex.py` — two-agent sequential crew

## Install + run

```bash
uv pip install -e ".[crewai]"
uv run python examples/c_advanced/crewai_with_pipelex_tools/run_crew_with_pipelex.py
```

Requires two API keys in `.env`:

- `PIPELEX_GATEWAY_API_KEY` — drives the Pipelex pipeline (`pipelex login` to get one)
- `OPENAI_API_KEY` — drives the CrewAI agent reasoning

After the run, check `reports/report.md` and `outbox.txt`.
