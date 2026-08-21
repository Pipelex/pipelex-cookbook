# Residual failures after the pipelex 0.41.0 sweep

Written during the workspace-wide sweep onto `pipelex` 0.41.0. This repo's pin crossed four release cycles (`==0.37.0` → `==0.41.0`). The address fixes landed and the suite improved sharply, but six tests remain red for two causes, **neither of which is an address fix and neither of which this sweep should fix**.

> **Resolved 2026-08-01 — the suite is green.** Both causes were closed in a follow-up pass, on Louis's call, with the pin now at `==0.42.0`. Cause 1 was worked around here by renaming the colliding fields; the generator bug itself is handed off to `pipelex` in [`wip/bugs/structure-field-name-shadows-type.md`](../../wip/bugs/structure-field-name-shadows-type.md) at the workspace root — **read that one, not the fix options below, which measurement has since corrected**. Cause 2 turned out to be a test-harness bug rather than stale bundle content. Details per cause below.

## Baseline: the suite was already red before the sweep

Measured, not assumed. With the pre-sweep tree checked out (`pipelex==0.37.0`) and the venv reinstalled:

```
48 failed, 6 skipped
! _pytest.outcomes.Exit: Critical Pipelex setup error: Could not create config of type
  <class 'pipelex.system.configuration.configs.PipelexConfig'> with provided data:
  Extra forbidden fields: 'pipelex.secrets_config'
```

The pinned 0.37.0 runtime could not even boot against the config shape on disk, so nearly the whole suite failed at setup. After the sweep: **6 failed, 50 passed, 6 skipped**. The sweep is a large net improvement; the residue below is pre-existing, not introduced here.

## Cause 1 — a pipelex codegen bug (upstream, needs a pipelex fix)

Four of the six: `extract_gantt` and `extract_invoice`, each failing both `test_dry_run` and `test_validate`; the integration `test_hello_world` fails for the same reason, because library setup loads every bundle.

```
pipelex.core.concepts.exceptions.ConceptFactoryError: Error generating python code for
structure class of concept 'Milestone' in domain 'gantt': Error validating generated code:
unsupported operand type(s) for |: 'FieldInfo' and 'NoneType'
```

The concept declares a field named `date` of type `date`:

```toml
[concept.Milestone.structure]
name = { type = "text", description = "The name of the milestone", required = true }
date = { type = "date", description = "The date of the milestone" }
```

and the structure-class generator emits:

```python
from datetime import date


class gantt__Milestone(StructuredContent):
    name: str = Field(..., description="The name of the milestone")
    date: date | None = Field(default=None, description="The date of the milestone")
```

**The generated code cannot execute.** In a class body, `x: T = v` binds `x` before the annotation `T` is evaluated, so by the time `date | None` is evaluated, `date` in the class namespace is the `FieldInfo` just assigned — not `datetime.date`. Any structure field whose name collides with the Python type name its own annotation references produces uncompilable code. `date` is simply the collision most likely to occur in real methods.

**Not a 0.41.0 regression.** The shape is broken identically on 0.37.0, 0.40.0 and 0.41.0 — verified by building the emitted class under each version. It is plain Python scoping, so no pipelex release fixed or introduced it; the sweep only made it *reachable*, because on 0.37.0 these bundles never got as far as codegen (the boot failure above stopped them first).

**Fix belongs in `pipelex`, not here.** ⚠ The three options originally sketched here were ranked by reasoning, not measurement, and two of them are wrong: module-qualification (then ranked first) still breaks on a field named `datetime`, and `from __future__ import annotations` (then ranked second) does not help at all, because pydantic resolves the deferred string against the class namespace too. The reserved-alias option, then ranked last, is the one that holds. The measured comparison and the suggested shape of the fix now live in [`wip/bugs/structure-field-name-shadows-type.md`](../../wip/bugs/structure-field-name-shadows-type.md) at the workspace root — **use that doc**, this paragraph is kept only so the superseded ranking is not re-derived from scratch.

**What was done here (2026-08-01).** Still broken on 0.42.0, and the cookbook consumes released pipelex from PyPI, so no upstream fix can turn this suite green today. Louis's call: rename the two colliding fields to unblock, and hand the generator bug off as the doc above rather than patching `pipelex` in the same pass.

- `Milestone.date` → `milestone_date` (also matches the sibling `GanttTaskDetails.start_date` / `end_date`)
- `Invoice.date` → `issue_date` (reads better beside `invoice_id` / `invoice_number` anyway)

No allowlist or skip was added: the `test_validate` gate still runs both bundles, so if someone renames a field back onto its own type name, it fails loudly with the same codegen error rather than silently regressing.

## Cause 2 — stale bundle content in `hello_world.mthds`

The remaining failure, `test_dry_run[examples/a_quick_start/hello_world.mthds]`:

```
Failed to execute pipeline 'hello_world': Input 'text' is not declared by this pipe.
Declared inputs: (none).
```

This was read at the time as authored content fallen behind the language, and deferred as a deliberate quick-start edit.

**It was neither (2026-08-01).** `hello_world` is correct as authored — it takes no inputs, and the README runs it with no `-i`. The bug was in the *test harness*: `test_bundles.py` attached `<bundle dir>/inputs.json` to every bundle in a folder, and `examples/a_quick_start/` holds two bundles — `hello_world`, which declares no inputs, and `summarize`, which that `inputs.json` actually belongs to. So the suite handed `summarize`'s `text` to `hello_world`, and passing a pipe an input it does not declare is (correctly) an error. Fixed by a `NO_INPUTS` opt-out in the harness, which makes the test run the bundle exactly the way the README documents it. No bundle content changed.

## What the sweep did change here

- Pin `pipelex[...]==0.37.0` → `==0.41.0`.
- `requires-python` `>=3.10` → `>=3.11` (plus the classifier and both CI matrices) — 0.41.0 requires `>=3.11`, so the 3.10 claim made the lock unsolvable.
- `pipelex.hub` split: `get_storage_provider` → `pipelex.runtime_hub`, `get_console` → `pipelex.runtime_hub`.
- `PipeRunMode` → `pipelex.system.pipe_run_mode`.

`make agent-check` is green.
