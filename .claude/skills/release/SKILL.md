---
name: release
description: >
  Cut a release of pipelex-cookbook, the examples and tutorials repo: the
  release/vX.Y.Z worktree, the pyproject.toml bump and the uv.lock that follows,
  the changelog entry, the lint and test gates, one commit, and a pull request to
  main that creates the GitHub Release on merge. Use when the user says
  "release", "cut a release", "bump version", "prepare a release", "new version",
  "make a release", "ship it", "create release branch", "promote dev to main", or
  any variation of shipping a new version of the cookbook. Changelog content
  passed inline ("/release Added an example for invoice extraction") becomes the
  entry. The merge is landed by /ledger-land, never by this skill.
---

# Releasing pipelex-cookbook

The procedure is the workspace release play, [`docs/releasing.md`](../../../../docs/releasing.md) at the workspace root — `../docs/releasing.md` from this repo's own root, which resolves the same from the main checkout and from any worktree. Read it first, then run it with what follows. The repo key is `pipelex-cookbook`, the base is `dev`, and the pull request targets `main`: `guard-branches.yml` refuses any head branch but `release/vX.Y.Z` into `main`, so there is no other way in. The release worktree is `_pipelex-cookbook--release`, made with `wt add pipelex-cookbook release --branch release/vX.Y.Z`. The repo declares neither `.worktree.toml` nor `.worktreeinclude`, so `wt` resolves the base from `origin/dev` and provisions with the Makefile's `install` target, which is what creates the `.venv` every gate below runs out of.

## What ships

Nothing is published to a package registry: there is no publish workflow in `.github/workflows/`, so the play's "the registry's answer" has no counterpart here. What the merge to `main` produces is the GitHub Release and its tag, created by `github-release.yml`, which fires on `push` to `main`:

- It reads the number with `grep -m 1 'version = ' pyproject.toml | cut -d '"' -f 2`, slices the changelog section between `## [vX.Y.Z] - ` and the next `## [v…] - ` heading for the notes, and calls `gh release create "v$VERSION"`.
- The notes keep the one blank line the step re-inserts after the version heading and lose every other, with leading and trailing whitespace stripped from each remaining line, so nested bullets flatten and a `###` subheading ends up against the bullets under it. When no `## [vX.Y.Z] - ` heading is found the step warns, sets the notes empty and exits 0, so the Release still ships — carrying the bare line `Release vX.Y.Z` instead of failing.
- Nothing guards the step against a Release that already exists, so a merge to `main` that does not carry a new number fails at `gh release create`. `guard-branches.yml` narrows the exposure by admitting only a `release/vX.Y.Z` head and `version-check.yml` ties that name to `pyproject.toml`, but neither compares the number against what `main` has already released, so re-merging a release branch for a version that already shipped is the way this step can still go red.

The landing verifies the publish from the run, the Release and the tag:

```bash
gh run list --workflow=github-release.yml --branch main --limit 3 --json conclusion,headSha,url  # the run whose headSha is the merge SHA: success
gh release view vX.Y.Z                                                                          # the Release and its notes
git fetch --tags --prune origin && git tag --list vX.Y.Z                                        # the tag
```

## Version files and the lock

- **`pyproject.toml`** — the `[project]` table's `version`, the one and only place the number is written, with no `v` prefix. Keep it the file's **first** `version = ` line and keep it at column zero: `github-release.yml` reads it with `grep -m 1 'version = '`, which `required-version` under `[tool.uv]` would otherwise match, and `version-check.yml` reads it with `grep '^version'`.
- **`uv.lock`** — the lockfile records the project's own version in its `pipelex-cookbook` entry, so it must be regenerated after the bump: `make lock` (`uv lock`), or `make li` (lock, then install) when the worktree's environment should be synced at the same time. If it fails, stop and report it rather than committing a stale lock.
- **Also stamped:** nothing. There is no README badge and no `__version__`. `requirements.txt` and `requirements-dev.txt` are exports of the lockfile made by `make export-requirements` and `make export-requirements-dev`, but they carry no version of the cookbook itself, so a bump leaves them untouched and they stay out of the release commit.

## Gates

Run in the worktree, in this order, before the commit:

1. `make agent-check` — `fix-unused-imports`, then `format` (`ruff format` and `plxt fmt`), `lint` (`ruff check --fix` and `plxt lint`), `pyright` and `mypy`. **It rewrites files**, so whatever it touched joins the release commit. Red blocks the release: fix the code, never loosen the target. The `plxt` half matters most here, because `lint-check.yml` runs only the ruff, pyright and mypy merge checks — the formatting and linting of the `.mthds` and TOML sources is enforced by this gate and nowhere else.
2. `make agent-test` — the pytest suite under the Makefile's usual markers, `"(dry_runnable or not inference) and not (needs_output or pipelex_api)"`, quiet unless it fails. `tests-check.yml` runs `make gha-tests` on the pull request across its 3.11, 3.12 and 3.13 matrix, and that target selects differently (`--disable-inference` with `-m "not inference and not gha_disabled"`), so a green run here is not a promise of a green matrix there — but a red one here is a red pull request.

## The release commit

`pyproject.toml`, `uv.lock`, `CHANGELOG.md`, and each file `make agent-check` rewrote — staged by name. The release commits on `main` carry the version file, the lock and the changelog and nothing else.

## CI on the release pull request

- `guard-branches.yml` (`gate-main`) — the head branch into `main` must match `^release\/v[0-9]+\.[0-9]+\.[0-9]+$` exactly, so the release branch name is the only way in. Its `gate-release` job governs pull requests whose base is `dev` or begins `release/v` instead, and `protect-workflows` fires only when the author association is `CONTRIBUTOR`.
- `version-check.yml` (pull requests to `main`) — the `pyproject.toml` version equals the version in the branch name. It asserts nothing about the version already on `main`. A head that is not a release branch does not slip past it: the `exit 0` in its first step ends that step alone, and the comparison that follows then fails on an empty branch version.
- `changelog-check.yml` (pull requests to `main`, and only when the head starts with `release/v`) — `CHANGELOG.md` carries a `## [vX.Y.Z] - ` heading for the version in the branch name. It asserts nothing about `[Unreleased]`; leaving none behind is the play's rule, not CI's.
- `lint-check.yml` (every pull request) — the ruff format, ruff lint, pyright and mypy merge checks on 3.11, 3.12 and 3.13, each leg installing with `make install`; the aggregator job `Lint (all versions)` is the single required status.
- `tests-check.yml` (every pull request) — `make gha-tests` on the same Python matrix with `ENV: dev`.
- `cla.yml` — the CLA assistant on `pull_request_target`, allowlisted for maintainers.

Nothing in CI checks that `uv.lock` agrees with `pyproject.toml` — no `uv lock --locked` runs anywhere, and `make install` re-locks silently rather than failing — so the lock step above is the only thing keeping the two in step.

## Particulars

- **The commit message carries a one-line summary**: `Release vX.Y.Z: <summary>`, which is where this repo departs from the play's bare `Release vX.Y.Z` and what its release commits on `main` read. Nothing in CI asserts it, so the summary is for the reader of the history.
- **No pre-release form.** A head like `release/v0.18.0-rc.1` fails all three release gates rather than skipping them: `guard-branches.yml` refuses it outright, `version-check.yml` compares the version against an empty branch version, and `changelog-check.yml` runs on any `release/v` head and then rejects the name against its own `^release/v([0-9]+\.[0-9]+\.[0-9]+)$`. Ship a plain `X.Y.Z`.
- **The changelog headings carry the `v`** — `## [vX.Y.Z] - YYYY-MM-DD` — which is exactly what `changelog-check.yml` greps for and what `github-release.yml` slices the Release notes out of. No `[Unreleased]` heading is left behind; the next change re-creates one.
- **The release tags are lightweight**, created as a side effect of `gh release create` rather than by `git tag -a`. Always pass `--tags` when reading them, and expect no loud failure without it: one annotated tag, `v0.1.7`, was pushed by hand early in the repo's history and is still reachable, so a bare `git describe` answers with that ancient tag instead of refusing, and the number it prints is not the last release.
- **`pipelex` is pinned exactly** — `pipelex[…]==A.B.C` in `[project].dependencies`, not a floor — so what a cookbook release usually promotes is that pin moving and the examples adapting to it. The pre-flight's log range is where to read which pin this release carries, and the changelog entry is mostly about that.
- **No release follow-ups are armed automatically.** `ledger.toml` declares no `release_followups` for `pipelex-cookbook`, so filing the release item materializes no blocked tasks; anything this release owes another repo is filed by hand alongside it.
