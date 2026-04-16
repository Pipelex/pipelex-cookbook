# CrewAI with Pipelex as a Typed Tool

A CrewAI agent calls a validated MTHDS pipeline via Pipelex. No custom parser, no lost semantics.

## Flow

1. **Author the bundle** — use the MTHDS skills (`/mthds-build`, `/mthds-check`) to design and validate `research.mthds`.
2. **Generate Pydantic structures** from the bundle's typed concepts:
   ```bash
   pipelex build structures research.mthds
   ```
   Output lands in `structures/<domain>__<concept>.py`. Remove the matching `[concept.X.structure]` block from the `.mthds` to avoid duplication — the Python class is now the source of truth.
3. **Give it to CrewAI** — decorate a function with `@tool`, import the Pydantic, call `PipelexRunner.execute_pipeline`, return the typed result.

## Why

Don't re-parse `.mthds` in Python just to plug into another framework — you lose validation, typed outputs, and batching. Let Pipelex own the bundle and expose it to CrewAI as a single typed tool.

| Concern | Owner |
|---|---|
| Parse, validate, run typed pipes, batch | Pipelex |
| Agent reasoning, tool choice | CrewAI |

## Files

- `research.mthds` — bundle (main pipe `deep_research`: gather → batch verify → synthesize)
- `structures/research__research_brief.py` — Pydantic `ResearchBrief(StructuredContent)`
- `run_crew_with_pipelex.py` — one `@tool` function returning the Pydantic

## Install + run

```bash
uv pip install -e ".[crewai]"
uv run python examples/c_advanced/crewai_with_pipelex_tools/run_crew_with_pipelex.py
```

Requires `PIPELEX_GATEWAY_API_KEY` (Pipelex inference) and `OPENAI_API_KEY` (CrewAI agent reasoning) in `.env`.
