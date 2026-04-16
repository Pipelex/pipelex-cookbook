# CrewAI with Pipelex as a Typed Tool

A CrewAI crew where a validated MTHDS pipeline sits between vanilla CrewAI agents.

## The crew

1. **Email Prep** (Pipelex-backed) — calls `prepare_customer_email`, a `PipeSequence` that runs a `PipeLLM` (analyze the review → typed `ReviewAnalysis`) followed by a `PipeCompose` (render a deterministic email body via a Jinja template). Same template, same structure every time.
2. **Email Dispatcher** (vanilla CrewAI) — has a `send_email` tool that writes to `outbox.txt` (a side effect Pipelex intentionally doesn't do). Takes the composed body from the prior task and dispatches it.

The two agents run sequentially. The split is clean:

| Layer | Responsibility | Example |
|---|---|---|
| Pipelex `PipeLLM` | Typed, validated LLM extraction | review → `ReviewAnalysis` |
| Pipelex `PipeCompose` | Deterministic template rendering (no LLM) | `ReviewAnalysis` → email body |
| CrewAI | Agent reasoning, tool choice, **side effects / external I/O** | send email, post to Slack, hit an API |

## Flow to build one of these

1. Author the bundle with the MTHDS skills: `/mthds-build`, `/mthds-check`.
2. Generate Pydantic structures:
   ```bash
   pipelex build structures review.mthds
   ```
   Output lands in `structures/<domain>__<concept>.py`. Remove the inline `[concept.X.structure]` block from the `.mthds` — the Python class is now the source of truth.
3. Wrap the pipe in a CrewAI `@tool` function that returns the Pydantic. Drop it into a crew with whatever other agents you need.

## Why

Don't re-parse `.mthds` in Python to plug into another framework — you lose validation, typed outputs, and batching. Let Pipelex own the bundle and expose it to CrewAI as one typed tool, then compose it with any other CrewAI agents / tools.

## Files

- `review.mthds` — bundle with the `analyze_review` pipe producing a typed `ReviewAnalysis`
- `structures/review__review_analysis.py` — Pydantic `ReviewAnalysis(StructuredContent)`
- `run_crew_with_pipelex.py` — two-agent sequential crew

## Install + run

```bash
uv pip install -e ".[crewai]"
uv run python examples/c_advanced/crewai_with_pipelex_tools/run_crew_with_pipelex.py
```

Requires `PIPELEX_GATEWAY_API_KEY` (Pipelex inference) and `OPENAI_API_KEY` (CrewAI agent reasoning) in `.env`. After the run, check `outbox.txt` — that's the customer email the CrewAI agent "sent".
