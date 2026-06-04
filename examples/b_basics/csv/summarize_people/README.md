# Summarize People — CSV in, CSV out

A minimal CSV round-trip. Pipelex reads a table of people from a CSV file, asks an LLM to summarize each one as a one-sentence persona, and writes the result back to a CSV.

## How it works

- **`inputs/people.csv`** is read straight into a typed list of `Person` (one item per row). When an input's `url` points at a `.csv` file, Pipelex auto-detects it and parses each row into the concept's structure.
- **`summarize_people`** (`PipeBatch`) runs one branch per person.
- Each branch (`summarize_person`, a `PipeSequence`) first calls **`describe_person`** (`PipeLLM`) to write a one-sentence persona, then **`compose_person_summary`** (`PipeCompose`) builds the output row, keeping only `name` and `country` from the original record plus the generated `summary` (dropping `job`, `birth_year`, `death_year`).
- The pipeline returns `PersonSummary[]`, which the `--save-csv` flag writes back out as a CSV.

CSV input/output works with **flat** concepts only — every field must be a scalar (`text`, `integer`, `number`, `boolean`, `date`). Both `Person` and `PersonSummary` here are flat.

## Run it

Writes the summaries to a CSV (needs `PIPELEX_GATEWAY_API_KEY` in your `.env`):

```bash
pipelex run bundle examples/b_basics/csv/summarize_people/summarize_people.mthds \
  -i examples/b_basics/csv/summarize_people/inputs.json \
  --save-csv results/people_summaries.csv
```

Dry run — no API key needed; still parses the input CSV and exercises the structure end to end:

```bash
pipelex run bundle examples/b_basics/csv/summarize_people/summarize_people.mthds \
  -i examples/b_basics/csv/summarize_people/inputs.json \
  --dry-run --save-csv results/people_summaries.csv
```

## Output

`results/people_summaries.csv` has the header `name,country,summary` and one row per input person, for example:

```csv
name,country,summary
Ada Lovelace,United Kingdom,A visionary Victorian mathematician who imagined computing long before the machines existed.
```

## Notes

- `--save-csv` requires a **list** output (`PersonSummary[]`) whose row concept is flat. Pointing it at a single record or a non-flat concept fails with a clear error.
- Relative `url` paths in `inputs.json` are resolved against the `inputs.json` file's own directory, so `inputs/people.csv` works regardless of where you run the command from.
