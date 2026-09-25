# Contributing to the Pipelex Cookbook

Thank you for sharing what you built. The cookbook holds worked examples of AI methods, written in MTHDS and run with Pipelex, that others can read, run and adapt, and it takes three kinds of contribution:

- **A method**: a package under `methods/<name>/` that anyone can run by address on the hosted API, with a sample to try it on and an answer key saying what a right result holds.
- **A recipe**: one way of using a method, under `recipes/<door>/<name>/`, shown on a real case.
- **A fix** to a page's template, to a recipe, or to a tutorial lesson.

The runtime itself lives in [Pipelex/pipelex](https://github.com/Pipelex/pipelex), and the method library in [Pipelex/methods](https://github.com/Pipelex/methods).

## Set up

1. Fork and clone this repository, then run `make install`, which installs the cookbook's tooling with `uv`. `make check-cookbook` also needs Node.js 22 with npm, and shellcheck, to type-check the recipes.
2. Copy `.env.example` to `.env` and put a `PIPELEX_API_KEY` in it, created in your console at [app.pipelex.com](https://app.pipelex.com). Only the checks that validate on production read it, and none of them spends inference.

[`docs/README.md`](docs/README.md) explains how the cookbook works: the packages, the generated pages, the recipes and every check.

## Add a method or a recipe

- **A method**: follow [`docs/adding-a-method.md`](docs/adding-a-method.md). It takes you through the package, the answer key written before the first run, the proof on production, the page, and the checks.
- **A recipe**: follow [`docs/adding-a-recipe.md`](docs/adding-a-recipe.md).

**Generated files are never edited by hand**: a method's `README.md`, everything under `tests/snippets/<name>/`, a recipe's `generated/` tree, and the two lists of methods on the front page. Change their sources, then run `make render`, or `make refresh` when a method's contract or a recipe's address changes.

## Before the pull request

1. Run `make agent-check`, `make agent-test` and `make check-cookbook`, which is what CI runs on your pull request, sample links included.
2. When your change touches a method, a page or a recipe, also run `make check-hosted`, with your key in `.env`. CI holds no key, so it cannot run these checks, and a maintainer runs them on your pull request too.
3. Add an entry under `## [Unreleased]` in `CHANGELOG.md`.

## Open the pull request

Open it against `dev`, from a branch named `feature/…`, `fix/…`, `docs/…`, `refactor/…`, `chore/…` or `ci-cd/…`; CI refuses any other name. A pull request from a fork cannot change `.github/workflows/`. The first time you open one, the CLA assistant asks you to sign the [Contributor License Agreement](CLA.md).

If you are unsure whether an idea fits, open a GitHub Discussion first.

## Communication channels

| Purpose                     | Where                                 |
| --------------------------- | ------------------------------------- |
| Ask "is this idea a fit?"   | GitHub **Discussions → Show & Tell**  |
| Report a cookbook bug       | GitHub **Issues**                     |
| Real-time chat / pairing    | **Discord** `#pipeline-contributions` |
| Private or security matters | `security@pipelex.com`                |

## Code of conduct

Be kind. All interactions fall under [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## Thank you!

Every method and recipe you add is one more thing someone can run in a minute and make their own.
