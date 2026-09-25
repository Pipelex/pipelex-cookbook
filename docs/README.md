# How the cookbook works

The cookbook holds Pipelex's example methods as packages anyone can run by address, and gives each one a page showing every way to use it: in a chatbot, in code, as an app, as a method of your own, and on your own machine. Beside the pages, recipes show one way of using a method in depth, on a real case, with code the checks hold to the method it calls. This document explains the parts that make that work. To add a method, read [adding-a-method.md](adding-a-method.md), and to add a recipe, [adding-a-recipe.md](adding-a-recipe.md).

The repository is mid-way through a rebuild. The older examples under `examples/`, with their runtime pin, their `.pipelex/` configuration and their tests, stay where they are until the new layout replaces them. Everything below describes the new layout.

## The packages

Each cookbook method is a package in `methods/<name>/`, laid out like the packages of the method library, [Pipelex/methods](https://github.com/Pipelex/methods), so that a method can move from one repository to the other by moving its directory:

| File | What it is |
|---|---|
| `METHODS.toml` | The manifest: `name`, `display_name`, `address`, `version`, `description`, `authors`, `license`, `mthds_version`, `main_pipe` and `[exports]` |
| `*.mthds` | The method's bundles |
| `inputs.json` | Sample inputs, each file linked by its raw URL on `main` under `assets/`, or by its own URL when it is a third-party file hosted elsewhere |
| `key.md` | The answer key for the sample, in the format of the Pipelex lab skill |
| `contract.json` | A snapshot of what the main pipe takes and returns, written by `make refresh` |
| `README.md` | The method's page, written by `make render` |

**The manifest is the method's identity.** The runtime finds a package by the `address` and `name` in its manifest, never by its directory, so every cookbook manifest carries `address = "github.com/Pipelex/pipelex-cookbook"` and a `name` equal to its directory's. The address `github.com/Pipelex/pipelex-cookbook/<name>@<tag>` then runs the method as it was at that release tag; without a tag it runs `main`'s head. A method on `dev` is not reachable by address until a release brings it to `main`.

**Versions are lockstep.** Every manifest's `version` is the cookbook's own, from `pyproject.toml`, as in the library: a manifest states the release it ships in. The release play sets them all.

**Every method meets the hosted bar.** A run by address refuses Python structure classes, and hosted execution does not yet serve a call to another package's pipes. So a cookbook method declares its types as MTHDS concepts, calls only its own pipes, and links its samples by URL.

## The pages

`methods/<name>/README.md` is generated, and so is every page: nobody edits one by hand. Each page follows the same order, one block per door: the header, with the method's address and its sample; "Try it in your chatbot"; "Put it in your code"; "Make it an app"; "Make it yours"; "What you get"; and "Run it on your own machine". Only the address, the samples and a few editorial lines change from one page to the next.

What a page says about its method comes from the package:

- **The address** is `address/name@tag`, where the tag is `v` followed by the version in `pyproject.toml`. On `dev` that is the latest release, since each release is merged back into `dev`; on a release branch it is the release being cut, and the release commit re-renders every page. A method added since the last release therefore names that release's tag, which does not hold it: `check-links` reports its links as not published and `check-addresses` its address as not released, rather than as broken, and the next release re-renders its page at the new tag.
- **"Takes" and "Returns"** come from the contract snapshot.
- **The samples and the code snippets' inputs** come from `inputs.json`.
- **"What you get"** is the answer key's `## Must` lines. The page shows them without the planted facts, so each Must line states its facts in full; the renderer refuses one that cites a planted fact such as `F2`.
- **The title, the pitch, the chatbot sentence and the "Make it yours" change** come from the method's entry in `cookbook.toml`. Every field is optional: a method with no entry gets its title and pitch from its manifest and a default sentence for the rest.

**The front page lists the methods.** `README.md` at the root is written by hand except for one region, between the markers `<!-- BEGIN methods, … -->` and `<!-- END methods -->`, where `make render` lists every method with its title, its page and its pitch, followed by a line linking the method library. `make check-render` holds that region to a fresh render as it does the pages, and leaves every other line of the front page alone.

Setup is never repeated on a page. Adding the Pipelex MCP, installing the plugin and creating a key are links to the front doors of [pipelex-mcp](https://github.com/Pipelex/pipelex-mcp) and [pipelex-plugins](https://github.com/Pipelex/pipelex-plugins), so a page carries only the commands that name its method.

## `cookbook.toml`

| Field | Meaning | Default |
|---|---|---|
| `address` | The address every cookbook manifest carries | Required |
| `repository` | The GitHub repository raw sample URLs point into | Required |
| `[methods.<name>].title` | The page's title | The manifest's `display_name` |
| `pitch` | The one-line pitch under the title | The manifest's `description` |
| `sample_labels` | The link text of each input's sample, by input name | "sample" and the input's name |
| `chatbot` | What to ask the chatbot, with `{address}`, `{samples}` and `{inputs_url}` placeholders | "Run {address} on {samples}", or on the sample inputs file when no input is a file |
| `app_dir` | The directory the method-app initializer creates | The name, dashed, with `-app` |
| `yours_dir` | The directory the agent copies the method into | The name |
| `yours_change` | The change "Make it yours" asks for | "adapt what it does to my case" |

An entry for a method that does not exist, or a field the renderer does not know, fails loudly.

## The renderer

The renderer is a small Python package in `scripts/`, run as `python -m scripts <command>` behind the Makefile's targets:

- `scripts/cookbook.py` loads the cookbook: the version, `cookbook.toml`, and every package, checking its identity with the MTHDS standard's own manifest parser.
- `scripts/key.py` reads an answer key.
- `scripts/contract.py` projects a validation verdict onto the main pipe's contract, and reads and writes `contract.json`.
- `scripts/render.py` derives each page's context and renders `templates/method_page.md.j2`, which includes one template per door from `templates/doors/`, and renders the front page's list of methods from `templates/front_region.md.j2`. Wording and links live in the templates; everything method-specific is computed in Python.
- `scripts/checks.py` holds the checks that need no key, and `scripts/hosted.py` the calls to production.

Its tests are in `tests/tooling/`. They build a small cookbook in a temporary directory, render it with the real templates, and boot no Pipelex runtime.

## The contract snapshot

The "Takes" and "Returns" lines come from production: `POST /v1/validate` answers a valid verdict whose `pipe_io_contracts` carries each pipe's inputs and output with their JSON schemas, and whose `input_form` view names each input's kind. `make refresh` validates each package from its files, projects the main pipe's entry into the small shape of `contract.json` (its inputs with their concepts and kinds, its output concept with its top-level fields and their types), and writes it beside the package. The renderer reads only committed files, so rendering, and the freshness check with it, needs no network and no key, and runs on any pull request, a fork's included.

`make refresh` is run by hand whenever a bundle changes what its main pipe takes or returns, followed by `make render`. `make check-methods` says when a snapshot no longer matches production.

## The recipes

A recipe is a small project under `recipes/<door>/<name>/`, grouped by the door it shows: `code/` for calling a method from your own code. Each has a `README.md` saying what it shows, what it needs, how to run it and what you get, and calls its method by an address pinned to a release tag, from the cookbook or from the method library, so the method never changes under it. A reader copies one directory and nothing else: a Python recipe is a single script declaring its dependencies inline, which `uv run` reads.

A code recipe carries the types of the method it calls, generated from that address, in `generated/<method>/`:

| File | What it is |
|---|---|
| `models.py` | The method's concepts as pydantic models, stamped by codegen. Never edited by hand |
| `codegen.lock` | The hash of every stamped file and the fingerprint of the method they were generated from |
| `sources.json` | The pinned address and the codegen target the tree comes from: the one file of the tree a person writes |
| `__init__.py` | Empty files making the tree importable as `generated.<method>`, which codegen never emits |

The script imports its types as `generated.<method>.models`, from the directory it runs in. `make refresh` regenerates every tree from its sidecar, through `POST /v1/codegen` with the address, and `make check-codegen` checks every tree against its lock with no key and no network. Both run `scripts/sdk/recipe_codegen.py`, the one piece of the tooling that uses `pipelex-sdk`, in an environment of its own made by `uv run --script`. Ruff never touches a generated tree, since a reformatted file no longer matches its lock.

Each Python recipe script is type-checked by pyright in the environment its own inline dependencies describe, under `recipes/pyrightconfig.json`, in strict mode: the check proves that the recipe calls the SDK as it is, and that it reads the method's result through the types generated from it.

## The checks

| Target | Needs | What it proves |
|---|---|---|
| `make check-render` | Nothing | Every committed page equals a fresh render |
| `make check-lockstep` | Nothing | Every manifest carries the cookbook's version |
| `make check-links` | The network | Every URL in the packages' inputs and every raw URL on the pages answers, following redirects. A URL into this repository must name a file this checkout holds; if it answers 404, it is reported as not published, since the next release publishes it |
| `make check-methods` | `PIPELEX_API_KEY` | Every package validates on production from its files, and its contract snapshot is current |
| `make check-recipes` | Nothing | Every recipe's generated tree has a sidecar naming an address pinned to a release tag and a target its language reads, the recipe's code calls that same address, and every Python recipe script declares `pipelex-sdk` |
| `make check-codegen` | Nothing | Every recipe's generated types still match their `codegen.lock`: no file edited, missing or left over |
| `make check-recipe-types` | The network, to install each script's dependencies | Every Python recipe script type-checks in strict mode, in its own environment |
| `make check-addresses` | `PIPELEX_API_KEY` | Every page's address validates on production at the page's tag, as a reader running it would reach it, and so does every address a recipe pins. A method the tag does not carry yet, or a tag not pushed yet, is reported as not released rather than failed: production answers the first with a 404 whose problem type is `method-package-not-found-error`, and the second with a `MethodFetchError` saying the tag names no git tag. Any other refusal fails |
| `make refresh` | `PIPELEX_API_KEY` | Rewrites every contract snapshot, and every recipe's generated types, from production |

`make check-cookbook` runs every check that needs no key, and is what the `Methods check` workflow runs on every pull request. `make agent-check` runs `check-render`, `check-lockstep`, `check-recipes` and `check-codegen` after the linters. The checks that call production, `check-methods` and `check-addresses`, are grouped under `make check-hosted`: CI holds no API key, so their author runs them by hand before each pull request, and the release play runs them at each release. After a release, `make check-addresses` is also what proves it: once the tag exists, every method must validate at it. None of them spends inference; running a method is a separate, deliberate act.

The tooling calls `POST /v1/validate` with `httpx` rather than through `pipelex-sdk`. The SDK pins an `mthds` release that the runtime this repository still pins for its older examples cannot run with, so the two cannot share one environment until that pin goes with the old examples. The recipes' codegen, which needs the SDK, runs in its own environment for the same reason.
