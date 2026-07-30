# Residual failures after the pipelex 0.41.0 sweep

Written during the workspace-wide sweep onto `pipelex` 0.41.0. This repo's pin crossed four release cycles (`==0.37.0` → `==0.41.0`). The address fixes landed and the suite improved sharply, but six tests remain red for two causes, **neither of which is an address fix and neither of which this sweep should fix**.

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

**Fix belongs in `pipelex`, not here.** Options for whoever picks it up, roughly in order of preference:

1. Emit a module-qualified annotation (`datetime.date | None` with `import datetime`), which no field name can shadow. Fixes the whole class of collisions at once.
2. Emit `from __future__ import annotations` and ensure the resolver evaluates against module globals rather than the class namespace.
3. Import the type under a reserved alias (`from datetime import date as _pipelex_date`).

Option 1 is the one that generalizes: the collision is not specific to `date`, and an allowlist of "risky field names" would rot.

Renaming the cookbook's field to dodge the collision would hide a bug every user of `type = "date"` can hit, so it is deliberately **not** done here.

## Cause 2 — stale bundle content in `hello_world.mthds`

The remaining failure, `test_dry_run[examples/a_quick_start/hello_world.mthds]`:

```
Failed to execute pipeline 'hello_world': Input 'text' is not declared by this pipe.
Declared inputs: (none).
```

This is authored content that has fallen behind the language: inputs must now be declared on the pipe. It is a genuine cookbook fix, but it is content authoring rather than an address re-point, so it is out of this sweep's scope — and it is the *quick-start* example, which deserves a deliberate edit rather than a drive-by one. Worth checking the other quick-start examples in the same pass.

## What the sweep did change here

- Pin `pipelex[...]==0.37.0` → `==0.41.0`.
- `requires-python` `>=3.10` → `>=3.11` (plus the classifier and both CI matrices) — 0.41.0 requires `>=3.11`, so the 3.10 claim made the lock unsolvable.
- `pipelex.hub` split: `get_storage_provider` → `pipelex.runtime_hub`, `get_console` → `pipelex.runtime_hub`.
- `PipeRunMode` → `pipelex.system.pipe_run_mode`.

`make agent-check` is green.
