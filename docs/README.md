# How the cookbook works

The cookbook holds Pipelex's example methods as packages anyone can run by address, and gives each one a page showing every way to use it: in a chatbot, in code, as an app, as a method of your own, and on your own machine. This document explains the parts that make that work. To add a method, read [adding-a-method.md](adding-a-method.md).

The repository is mid-way through a rebuild. The older examples under `examples/`, with their runtime pin, their `.pipelex/` configuration and their tests, stay where they are until the new layout replaces them. Everything below describes the new layout.

## The packages

Each cookbook method is a package in `methods/<name>/`, laid out like the packages of the method library, [Pipelex/methods](https://github.com/Pipelex/methods), so that a method can move from one repository to the other by moving its directory:

| File | What it is |
|---|---|
| `METHODS.toml` | The manifest: `name`, `display_name`, `address`, `version`, `description`, `authors`, `license`, `mthds_version`, `main_pipe` and `[exports]` |
| `*.mthds` | The method's bundles |
| `inputs.json` | Sample inputs, each file linked by its raw URL on `main` under `assets/` |
| `key.md` | The answer key for the sample, in the format of the Pipelex lab skill |
| `contract.json` | A snapshot of what the main pipe takes and returns, written by `make refresh` |
| `README.md` | The method's page, written by `make render` |

**The manifest is the method's identity.** The runtime finds a package by the `address` and `name` in its manifest, never by its directory, so every cookbook manifest carries `address = "github.com/Pipelex/pipelex-cookbook"` and a `name` equal to its directory's. The address `github.com/Pipelex/pipelex-cookbook/<name>@<tag>` then runs the method as it was at that release tag; without a tag it runs `main`'s head. A method on `dev` is not reachable by address until a release brings it to `main`.

**Versions are lockstep.** Every manifest's `version` is the cookbook's own, from `pyproject.toml`, as in the library: a manifest states the release it ships in. The release play sets them all.

**Every method meets the hosted bar.** A run by address refuses Python structure classes, and hosted execution does not yet serve a call to another package's pipes. So a cookbook method declares its types as MTHDS concepts, calls only its own pipes, and links its samples by URL.

## The pages

`methods/<name>/README.md` is generated, and so is every page: nobody edits one by hand. Each page follows the same order, one block per door: the header, with the method's address and its sample; "Try it in your chatbot"; "Put it in your code"; "Make it an app"; "Make it yours"; "What you get"; and "Run it on your own machine". Only the address, the samples and a few editorial lines change from one page to the next.

What a page says about its method comes from the package:

- **The address** is `address/name@tag`, where the tag is `v` followed by the version in `pyproject.toml`. On `dev` that is the latest release, since each release is merged back into `dev`; on a release branch it is the release being cut, and the release commit re-renders every page. A method added since the last release therefore names a tag it is not in yet, which the checks report as not published rather than as broken.
- **"Takes" and "Returns"** come from the contract snapshot.
- **The samples and the code snippets' inputs** come from `inputs.json`.
- **"What you get"** is the answer key's `## Must` lines. The page shows them without the planted facts, so each Must line states its facts in full; the renderer refuses one that cites a planted fact such as `F2`.
- **The title, the pitch, the chatbot sentence and the "Make it yours" change** come from the method's entry in `cookbook.toml`. Every field is optional: a method with no entry gets its title and pitch from its manifest and a default sentence for the rest.

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
- `scripts/render.py` derives each page's context and renders `templates/method_page.md.j2`, which includes one template per door from `templates/doors/`. Wording and links live in the templates; everything method-specific is computed in Python.
- `scripts/checks.py` holds the checks that need no key, and `scripts/hosted.py` the calls to production.

Its tests are in `tests/tooling/`. They build a small cookbook in a temporary directory, render it with the real templates, and boot no Pipelex runtime.

## The contract snapshot

The "Takes" and "Returns" lines come from production: `POST /v1/validate` answers a valid verdict whose `pipe_io_contracts` carries each pipe's inputs and output with their JSON schemas, and whose `input_form` view names each input's kind. `make refresh` validates each package from its files, projects the main pipe's entry into the small shape of `contract.json` (its inputs with their concepts and kinds, its output concept with its top-level fields and their types), and writes it beside the package. The renderer reads only committed files, so rendering, and the freshness check with it, needs no network and no key, and runs on any pull request, a fork's included.

`make refresh` is run by hand whenever a bundle changes what its main pipe takes or returns, followed by `make render`. `make check-methods` says when a snapshot no longer matches production.

## The checks

| Target | Needs | What it proves |
|---|---|---|
| `make check-render` | Nothing | Every committed page equals a fresh render |
| `make check-lockstep` | Nothing | Every manifest carries the cookbook's version |
| `make check-links` | The network | Every raw URL in the packages and on the pages answers. A URL into this repository must name a file this checkout holds; if it does not answer yet, it is reported as not published, since a release brings it there |
| `make check-methods` | `PIPELEX_API_KEY` | Every package validates on production from its files, and its contract snapshot is current |
| `make refresh` | `PIPELEX_API_KEY` | Rewrites every contract snapshot from production |

`make check-cookbook` runs the three that need no key, and is what the `Methods check` workflow runs on every pull request. `make agent-check` runs `check-render` and `check-lockstep` after the linters. The checks that call production are grouped under `make check-hosted`: CI holds no API key, so their author runs them by hand before each pull request, and the release play runs them at each release. None of them spends inference; running a method is a separate, deliberate act.

The tooling calls `POST /v1/validate` with `httpx` rather than through `pipelex-sdk`. The SDK pins an `mthds` release that the runtime this repository still pins for its older examples cannot run with, so the two cannot share one environment until that pin goes with the old examples.
