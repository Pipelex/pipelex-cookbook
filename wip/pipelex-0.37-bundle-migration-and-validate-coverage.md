# Plan: migrate cookbook bundles to pipelex 0.37 + close the `validate` coverage gap

## Status: DONE

All phases complete. Summary of what actually happened (some of the plan's hypotheses did not hold — see the outcome table):

- **The only real 0.37 break was the PipeParallel-output rule.** No bundle tripped the main-stuff invariant, and there were no leftover `combined_output` lines anywhere. The two "non-parallel failures" the plan flagged (`advisory_board`, `validate_expense_data`) turned out **not** to be 0.37 breaks at all — they are validation-harness artifacts (a multi-file bundle and a PipeFunc bundle). `due_diligence/report.mthds` failed only transitively, because its sibling `analysis.mthds` was broken and it was being validated in isolation.
- **`Composite` for the methods, typed `PoemSet` for the tutorial** (decision taken with the user). The methods' combined composite is never consumed structurally — downstream steps read the individual branch results by name via `add_each_output = true` — so `Composite` is the honest, minimal fix. The tutorial's parallel is the terminal output over three homogeneous `Text` branches, so a typed `PoemSet { haiku, limerick, sonnet }` reads best. Note: a typed composite's fields must be `concept`-typed (`concept_ref = "Text"`), **not** scalar `text` — a scalar `text` field passes blueprint validation but fails the dry run because a branch produces a `Text` *stuff*, not a raw string.
- **`pipelex validate bundle` already runs an internal dry run**, so static validation catches runtime-shape breaks (like the scalar-`text`-field mistake above) without any inputs or LLM keys. That resolves the plan's open question #4: validate-only *is* a dry-run smoke test.
- **The gate is a non-inference pytest test** (`tests/e2e/test_validate_bundles.py`), which is what makes it run in CI: `make gha-tests` filters `-m "not inference"`, so the pre-existing dry-run suite (`test_bundles.py`, marked `inference`) never gated CI — and it only ever walked `examples/`, never `tutorial/` or `.mthds/methods/`. The new test walks all three roots, validates each bundle with `-L <parent dir>` (to resolve multi-file cross-refs), and reports `examples/wip/` as documented SKIPs.
- **`examples/wip/` is excluded from the gate, documented** (decision taken with the user). `advisory_board` validates clean as a multi-file bundle and `validate_expense_data` needs its Python `@pipe_func`s registered at runtime; neither needs a code fix.

**Post-migration cleanup (done):** the four migrated method packages (`doc_summarizer`, `doc_comparator`, `rfp_qualifier`, `due_diligence`) plus five other installed methods turned out to be referenced by nothing in the cookbook, so those **nine** packages were **removed** (per user decision) — they are installed copies whose canonical source is the `github.com/Pipelex/methods` repo + the MTHDS Hub. The one method that stays is **`documents`**: the `examples/b_basics/document_extract/*` bundles resolve it by address (`github.com/Pipelex/methods/documents->documents.extract_*`), a deliberate demonstration of referencing a shared Hub method. The validation gate covers `tutorial/` and `examples/` (the latter transitively exercises `documents` via that resolution).

**Still open (out of scope for this repo):** the parallel-using packages published to the MTHDS Hub are still broken against 0.37 for anyone who installs and runs them, and must be **republished** from their canonical source (the `methods` repo), independent of this cookbook cleanup. (Their fixes are no longer carried here — the packages were removed.)

## Why this exists

The cookbook is pinned to `pipelex==0.37.0` (see `pyproject.toml`), which shipped **breaking MTHDS language changes**. `make check`, `make test`, and `make validate` are all green — but that is a **false positive**: several example/method bundles fail `pipelex validate bundle` and the green gates never touch them. This plan fixes the broken bundles (workstream A) and widens the validation gate so this class of drift can't slip through green again (workstream B).

This is a handoff note. The findings below were gathered from outside the repo; **start by reproducing them here**, then dig into the per-bundle specifics.

## The two things that broke bundles in 0.37

Authoritative source: the **pipelex `CHANGELOG.md`, `0.37.0` "Breaking" entries** — read those first. In short:

1. **`PipeParallel` must combine into a `Composite` or a structured concept.** A parallel's declared `output` is now strictly validated at author time: it must be the native `Composite` concept, or a structured concept whose fields/types match the branch `result` names. It may **not** be a scalar native (`Text`, `Dynamic`, `Anything`, `Page`, …) and may **not** carry a multiplicity (`Foo[]` — a list aggregation is `PipeBatch`'s shape). The removed `combined_output` field is replaced by this combination, and `add_each_output` now defaults to `false`. Migration for an `add_each_output`-only pipe: replace the placeholder `output` with `Composite` (or a matching structured concept). (`Composite.is_composite == True`; `Dynamic`/`Anything`/`Text`/`Page` are all `False`.)
2. **Main-stuff invariant enforced end to end.** Every completed run must deliver a `main_stuff`; wire models make `main_stuff_name` required and `PipeOutput.optional_main_stuff` is gone. A bundle whose main pipe can finish without a main stuff will now fail.

The parallel-output rule is the confirmed cause for the two bundles diagnosed so far; the main-stuff invariant (and/or leftover `combined_output` lines) is the likely cause for the non-parallel failures — **confirm per bundle in Phase 0**.

## The coverage gap (why CI stayed green)

`make validate` runs `pipelex validate --all`, which only validates the **configured library pipelines**. It does **not** walk `tutorial/`, `examples/`, `quick_start/`, or the installed method packages under `.mthds/methods/`. Those directories hold ~34+ loose bundles that no gate exercises. `make check` is Python-only (`format lint pyright mypy`) and never looks at `.mthds` at all. So a released breaking language change sailed through.

## Reproduce (do this first)

Per-bundle verdict (note: `validate --all` will NOT surface these):

```
pipelex validate bundle <path-to.mthds>
```

Sweep every loose/method bundle and list failures:

```
for f in $(find tutorial examples quick_start .mthds -name "*.mthds"); do
  PIPELEX_NO_DECK_NOTICE=1 .venv/bin/pipelex validate bundle "$f" 2>&1 | grep -q "❌" && echo "FAIL $f"
done
```

## Currently-failing bundles (the work list) — FINAL

Outcome table (bundle → exact cause → fix applied):

| Bundle | Pipe(s) | Cause | Fix |
| --- | --- | --- | --- |
| `tutorial/medium/3_parallel_execution.mthds` | `generate_poems_parallel` | parallel-output — `output = "Dynamic"` | Added typed concept `PoemSet` (three `concept`-typed `Text` fields matching the branch result names); `output = "PoemSet"`. |
| `.mthds/methods/doc_summarizer/bundle.mthds` | `analyze_in_parallel` | parallel-output — `output = "Anything"` | `output = "Composite"`. |
| `.mthds/methods/doc_comparator/bundle.mthds` | `extract_both` | parallel-output — `output = "Page[]"` (multiplicity) | `output = "Composite"`. |
| `.mthds/methods/rfp_qualifier/bundle.mthds` | `extract_documents` | parallel-output — `output = "Page[]"` (multiplicity) | `output = "Composite"`. |
| `.mthds/methods/due_diligence/analysis.mthds` | `extract_all_documents`, `analyze_all` | parallel-output — `Page[]` + `Anything` | `output = "Composite"` on both. |
| `.mthds/methods/due_diligence/report.mthds` | — | **not a direct break**: cross-references `due_diligence_analysis.FinancialSnapshot` from the broken `analysis.mthds`, validated in isolation | No edit. Passes once `analysis.mthds` is fixed and the method is validated as a unit (`-L` / `validate method`). |
| `examples/wip/advisory_board/bundle.mthds` | — | **not a 0.37 break**: multi-file bundle referencing `presentation.MarkdownReport` in a sibling file | No edit. Validates clean with `-L <dir>`. Excluded from the gate (wip). |
| `examples/wip/validate_expense_data/validation.mthds` | — | **not a 0.37 break**: PipeFunc bundle; `@pipe_func` functions (e.g. `extract_expenses_list`) are only registered at runtime, so static validation can't resolve them | No edit. Excluded from the gate (wip). |

No bundle tripped the **main-stuff invariant**, and there were **no `combined_output` lines** anywhere. Everything else validated clean.

## Plan

### Phase 0 — reproduce & classify

Reproduce the sweep above so the failing set is current (bundles may have moved). For each failing bundle, capture the exact validation error and tag it: `parallel-output`, `main-stuff`, `combined_output`, or `other`. Produce a small table (bundle → cause → intended fix) before editing anything. This table is the real spec for Phases 1–2.

### Phase 1 — migrate the PipeParallel bundles

For each `parallel-output` failure, change the `PipeParallel`'s `output`:

- Fastest correct fix: `output = "Composite"` (accepts any branch `result` names; no field-matching).
- **Preferred for teaching quality:** a typed structured concept whose fields are the branch result names (e.g. a `PoemSet { haiku, limerick, sonnet }`). The cookbook is instructional material — a named structured output reads far better than the generic `Composite`, and it exercises the feature the way we'd want a reader to copy. **Decide per bundle** (see open questions); `Composite` is an acceptable fallback where a typed shape adds noise.

Drop any leftover `combined_output` line, and check whether `add_each_output` is still needed (it now defaults to `false`, so downstream steps that read a branch result by name via working memory need `add_each_output = true` explicitly). After each edit, re-validate the bundle AND confirm downstream steps that consume the combined/branch outputs still resolve.

### Phase 2 — migrate the remaining bundles

For the non-parallel failures, apply the migration matching the Phase 0 cause (most likely: ensure the main pipe yields a main stuff; remove dead `combined_output`). `due_diligence/report`, `advisory_board`, and `validate_expense_data` are the ones to look at closely — they aren't obviously parallel, so treat them as their own diagnosis.

> **Checkpoint — bundles migrated.** Success criterion: the Phase 0 sweep reports zero failures (or only the intentionally-excluded `examples/wip/` set, if that decision lands that way). Re-run `make check` and `make test` green. Update this doc's work-list with the final per-bundle causes/fixes before moving on.

### Phase 3 — close the coverage gap

Widen the validation gate so tutorials, examples, and installed methods are covered:

- Investigate how `pipelex validate --all` scopes its library, and pick the cleanest way to also validate the loose dirs. Two shapes to weigh: (a) a `validate` make target that walks `tutorial/`, `examples/`, `quick_start/`, `.mthds/methods/` and runs `pipelex validate bundle` on each (mirrors the sweep above); (b) if pipelex supports pointing `validate` at explicit dirs, prefer that over a hand-rolled loop.
- Wire it into whatever gate the repo runs in CI so a future breaking language change fails loudly here instead of in a reader's terminal.
- **Decide the `examples/wip/` policy.** `advisory_board` and `validate_expense_data` live under `examples/wip/` — they may be intentionally incomplete. Either fix them and gate them, or explicitly exclude `examples/wip/` from the widened target (and say so in the target/docs, per the "no silent caps" habit — don't let an exclusion read as "everything passes").

### Phase 4 — verify & flag Hub

Full sweep → zero failures (modulo documented exclusions); `make check`, `make test`, `make validate` all green. Then flag the downstream: the `.mthds/methods/*` packages are almost certainly the same methods published to the **MTHDS Hub** — if so, the Hub copies are broken against 0.37 for anyone who installs and runs them, and need republishing after this fix. That republish is out of scope for this repo but must not be dropped; note it wherever Hub publishing is tracked.

## Open questions / decisions for whoever picks this up

- **`Composite` vs typed structured output** per parallel — teaching clarity vs. minimal diff. Lean typed for the polished tutorials/methods, `Composite` for throwaway/wip.
- **`examples/wip/` policy** — fix-and-gate, or exclude-and-document.
- **Hub republish** — are these methods published? Who owns the republish once the bundles are fixed?
- **Scope of the widened gate** — validate-only, or also a smoke `--dry` run where feasible (dry run would also catch runtime-shape breaks the static validator misses).

## References

- pipelex `CHANGELOG.md` → `0.37.0` "Breaking" entries (PipeParallel combination, main-stuff invariant, Orchestrator SPI split).
- Rule source in installed pipelex: `pipelex/pipe_controllers/parallel/pipe_parallel_blueprint.py` (`validate_output`) and `pipe_parallel.py` (`validate_output_with_library`).
