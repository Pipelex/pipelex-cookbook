# How the cookbook works

The cookbook holds Pipelex's example methods as packages anyone can run by address, and gives each one a page showing every way to use it: in a chatbot, in code, as an app, as a method of your own, and on your own machine. Beside the pages, recipes show one way of using a method in depth, on a real case, calling it by an address the checks hold to a release tag. This document explains the parts that make that work. To add a method, read [adding-a-method.md](adding-a-method.md), and to add a recipe, [adding-a-recipe.md](adding-a-recipe.md).

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
- **The samples and the code snippets' inputs** come from `inputs.json`. When the inputs, written as JSON, run longer than `INLINE_INPUTS_LIMIT` in `scripts/render.py`, the snippets do not write them out: the TypeScript, Python and HTTP snippets all fetch them from the raw `inputs.json` at the page's tag, the file "Run it on your own machine" links and `make check-links` fetches, and send them as they are, `{concept, content}` wrappers included.
- **"What you get"** is the answer key's `## Must` lines. The page shows them without the planted facts, so each Must line states its facts in full; the renderer refuses one that cites a planted fact such as `F2`.
- **The title, the pitch, the chatbot sentence and the "Make it yours" change** come from the method's entry in `cookbook.toml`. Every field is optional: a method with no entry gets its title and pitch from its manifest and a default sentence for the rest.

**The code snippets are written as files too.** The TypeScript and Python snippets of "Put it in your code" come from `templates/snippets/`, which the page includes inside its fences and which `make render` also writes, under a header saying where they come from, as `tests/snippets/<name>/typescript/snippet.ts` and `tests/snippets/<name>/python/snippet.py`. The Python file opens with the inline dependencies `uv run` reads. Like the pages, these files are never edited by hand: `make check-render` holds them to a fresh render, and fails on a directory under `tests/snippets/` that belongs to no method, since `make render` never deletes one.

**Each snippet file reads the output through the method's types.** Below the page's snippet, which it holds verbatim, each file reads the result's `main_stuff` as the concept the page's "Returns" line names: the TypeScript file through the `parse…` function of the generated binder, and the Python file in a `read_output` function returning the generated model, since the page's `result` lives inside `main`. A list output is read both as a bare list and as the `{"items": [...]}` envelope, as the recipes read one. The page never shows this read, so a reader copies a snippet that needs no generated types, while the type checkers hold the read to the types of the concept it names. That concept is the main pipe's declared output: loading the cookbook, which every command does, refuses a `contract.json` whose main pipe, output concept or multiplicity is not what the package's `.mthds` files declare, so a bundle changed without `make refresh` fails `make check-render` in CI, not only the keyed checks. What no offline check can hold is what a run returns: both SDKs type `main_stuff` loosely, so the read validates the output only when it runs, and the page's call names the last release's tag while the types come from the files on the branch. The types sit beside each file, in `tests/snippets/<name>/<language>/generated/<name>/`, laid out as a code recipe's are (see [the recipes](#the-recipes)), except that their `sources.json` is written by `make render` and names the package's `.mthds` files, by their paths from the repository root, instead of an address: a page names the last release's tag, which does not hold a method added since, so types taken from the page's address could not be generated for it. `make check-render` holds each sidecar to its package, `make refresh` generates the types from the files, `make check-codegen` checks them against their lock, and `make check-codegen-live` catches a bundle changed without a refresh.

`make check-recipe-types` type-checks the snippet files as it does the recipes, so a page never shows a call the SDK it names no longer takes, or reads an output concept its method's types no longer hold: each `snippet.py` with pyright in strict mode, in the environment its inline dependencies describe, under `tests/snippets/pyrightconfig.json`, which extends the recipes' configuration and roots the import of `generated.<name>` beside each file; and every `snippet.ts` with `tsc --noEmit` in the one TypeScript package `tests/snippets/` holds, whose `package.json`, `package-lock.json`, `tsconfig.json`, `pyrightconfig.json` and `README.md` are written by hand and pin `@pipelex/sdk` as the TypeScript recipes do. The package runs no `codegen:check` script: `make check-codegen` already checks every tree against its lock, and the gate's other half, which compares a sidecar's recorded source hashes with the bundle, has nothing to compare in a sidecar that records none. The Python SDK types an input as a string, a list of strings, a content object or a list of them, or a dict, so it refuses a sample passing a list of plain objects, such as several documents given by their URLs, although the hosted API reads one. Such a sample's `snippet.py` says so in a comment and leaves argument types unchecked, rather than its page showing a detour a reader does not need.

**The front page lists the methods.** `README.md` at the root opens with the hosted doors, each set up in the words of the onboarding blocks it adapts, as its stamp comment says, and ends with running a method on your own machine. It is written by hand except for two regions. Between the markers `<!-- BEGIN methods, … -->` and `<!-- END methods -->`, `make render` lists every cookbook method with its title, its page and its pitch. Between `<!-- BEGIN library, … -->` and `<!-- END library -->`, it lists the method library's methods, each with a link to its directory and its address at the library tag `cookbook.toml` pins, from the snapshot `library.json`. `make check-render` holds both regions to a fresh render as it does the pages, and leaves every other line of the front page alone.

**The library's list comes from a snapshot.** `[library]` in `cookbook.toml` pins the library's address, its repository and a release tag, and `library.json`, beside it, holds the name, display name, description and main pipe of each method at that tag. `make refresh-library` takes the snapshot: it downloads the tag's tarball from the library's repository on GitHub, which needs no key, reads every `methods/<name>/METHODS.toml` in it in memory with the standard's manifest parser, and refuses a manifest whose name is not its directory's, whose address is not the pinned one or whose version is not the tag's. Rendering reads only the snapshot, so the front page renders with no network, and loading the cookbook refuses a snapshot taken from another repository, address or tag than the one pinned, naming `make refresh-library` as the cure. `make check-library` takes the snapshot again and fails when `library.json` differs from it, so a hand edit fails CI as a hand edit to a page does. To list a newer library release, move the tag, then run `make refresh-library` and `make render`; `make check-addresses` then validates each listed address on production.

Setup is never repeated on a page. Adding the Pipelex MCP, installing the plugin and creating a key are links to the front doors of [pipelex-mcp](https://github.com/Pipelex/pipelex-mcp) and [pipelex-plugins](https://github.com/Pipelex/pipelex-plugins), so a page carries only the commands that name its method.

## `cookbook.toml`

| Field | Meaning | Default |
|---|---|---|
| `address` | The address every cookbook manifest carries | Required |
| `repository` | The GitHub repository raw sample URLs point into | Required |
| `[library].address` | The address every library manifest carries | Required |
| `[library].repository` | The library's GitHub repository, whose tagged tarball the snapshot is taken from | Required |
| `[library].tag` | The library release the front page lists | Required |
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
- `scripts/contract.py` projects a validation verdict onto the main pipe's contract, and reads and writes `contract.json`. `scripts/bundles.py` reads the main pipe's declared output from the package's `.mthds` files, which loading the cookbook holds each `contract.json` to.
- `scripts/render.py` derives each page's context and renders `templates/method_page.md.j2`, which includes one template per door from `templates/doors/`, and renders the front page's two lists, of the cookbook's methods from `templates/front_region.md.j2` and of the library's from `templates/library_region.md.j2`. The code door includes its TypeScript and Python snippets from `templates/snippets/`, where `file.ts.j2` and `file.py.j2` wrap the same snippets, with the typed read the page does not show, into the files under `tests/snippets/`, and `sources.json.j2` writes the sidecar of each one's generated tree. Wording and links live in the templates; everything method-specific is computed in Python.
- `scripts/library.py` takes the library's snapshot from its tarball, and loads and checks `library.json`.
- `scripts/checks.py` holds the checks that need no key, and `scripts/hosted.py` the calls to production.

Its tests are in `tests/tooling/`. They build a small cookbook in a temporary directory, render it with the real templates, and call no API.

## The contract snapshot

The "Takes" and "Returns" lines come from production: `POST /v1/validate` answers a valid verdict whose `pipe_io_contracts` carries each pipe's inputs and output with their JSON schemas, and whose `input_form` view names each input's kind. `make refresh` validates each package from its files, projects the main pipe's entry into the small shape of `contract.json` (its inputs with their concepts and kinds, its output concept with its top-level fields and their types), and writes it beside the package. Loading the cookbook holds each snapshot to the package's files: its main pipe, its output concept and its multiplicity must be what the `.mthds` files declare, a bare concept resolving as the standard resolves one, to a native concept first and then to one of the bundle's domain, so a bundle whose main pipe's output changed without `make refresh` fails every command but `make refresh` itself, which loads without the snapshots in order to rewrite them. The renderer reads only committed files, so rendering, and the freshness check with it, needs no network and no key, and runs on any pull request, a fork's included.

`make refresh` is run by hand whenever a bundle changes. It writes the snapshots, then renders, since the pages read the snapshots and the page snippets' sidecars name the package's files, then regenerates the types of every recipe and page snippet. `make check-methods` says when a snapshot no longer matches production, and `make check-codegen-live` when a page snippet's types no longer come from its package's files as they are.

## The recipes

A recipe lives under `recipes/<door>/<name>/`, grouped by the door it shows: `run/` for running a method from a coding agent or over HTTP, `code/` for calling one from your own code, `app/` for making one into a web app, and `yours/` for making one your own. Each has a `README.md` saying what it shows, what it needs, how to run it, what you get and how it is built, and calls its method by an address pinned to a release tag, from the cookbook or from the method library, so the method never changes under it. A reader copies one directory and nothing else: a Python recipe is a single script declaring its dependencies inline, which `uv run` reads, and a TypeScript recipe is a small package with its `package.json` and `package-lock.json`, which `npm install` reads.

A recipe whose door needs no code of the reader's own, such as a request to a coding agent, an app the method-app template writes or a method made your own, is its README alone, whose "How it is built" names the tools or the routes underneath; the HTTP recipe carries a POSIX shell script besides. The checks read every recipe's README, shell scripts and JSON files as well as its code: each address they name with a tag must carry a release tag, `vX.Y.Z`, and `make check-addresses` validates it on production; each shell script must parse under `sh -n` and pass shellcheck; and every raw URL in a recipe's files must answer, as the pages' do. An address without an `@`, such as a repository link, names no tag and is not read as one, and neither is a catalog id (`mt_…`).

A code recipe carries the types of the method it calls, generated from that address, in `generated/<method>/`:

| File | What it is |
|---|---|
| `models.py` | For a Python recipe, the method's concepts as pydantic models, stamped by codegen. Never edited by hand |
| `types.ts`, `binder.ts` | For a TypeScript recipe, the method's concepts as zod schemas and their types, and a `parse…` function per concept, stamped by codegen. Never edited by hand |
| `codegen.lock` | The hash of every stamped file and the fingerprint of the method they were generated from |
| `sources.json` | The pinned address and the codegen target the tree comes from: the one file of the tree a person writes |
| `__init__.py` | For a Python recipe, empty files making the tree importable as `generated.<method>`, which codegen never emits |

A Python script imports its types as `generated.<method>.models`, from the directory it runs in, and TypeScript code imports them from `generated/<method>/binder` and `types`. `make refresh` regenerates every tree from its sidecar, through `POST /v1/codegen` with the address, `make check-codegen` checks every tree against its lock with no key, and `make check-codegen-live` asks production whether each lock records the crate its address resolves to today, which catches a sidecar pointed at another address without a regeneration. The page snippets' trees go through the same three, except that their sidecar names `method.files`, the package's `.mthds` files by their paths from the repository root, where a recipe's names `method.method_ref`: the script sends those files' contents to `POST /v1/codegen`, and refuses a sidecar naming both, neither, or a file that is not a `.mthds` file under `methods/`. All three run `scripts/sdk/recipe_codegen.py`, the one piece of the tooling that uses `pipelex-sdk`, from the repository root, in an environment of its own made by `uv run --script`, which needs the network the first time it installs the SDK. Ruff never touches a generated tree, since a reformatted file no longer matches its lock.

Each Python recipe script is type-checked by pyright in the environment its own inline dependencies describe, under `recipes/pyrightconfig.json`, in strict mode: the check proves that the recipe calls the SDK as it is, and that it reads the method's result through the types generated from it. Each TypeScript recipe package is installed with `npm ci` from its own lock, then runs its `codegen:check` script, the `pipelex-integrate` skill's `codegen-check.mjs` copied into `scripts/` as it is, which checks each of its trees against their lock with `@pipelex/sdk`, and `tsc --noEmit` under its own strict `tsconfig.json`.

## The checks

| Target | Needs | What it proves |
|---|---|---|
| `make check-render` | Nothing | Every committed page, snippet file and snippet sidecar, and both of the front page's lists, equal a fresh render, and every directory under `tests/snippets/` belongs to a method |
| `make check-lockstep` | Nothing | Every manifest carries the cookbook's version |
| `make check-library` | The network | `library.json` equals a fresh snapshot of the library's tarball at the tag `cookbook.toml` pins |
| `make check-links` | The network | Every URL in the packages' inputs, and every raw URL on the pages and in the recipes' own files, answers, following redirects. A URL into this repository must name a file this checkout holds; if it answers 404, it is reported as not published, since the next release publishes it |
| `make check-methods` | `PIPELEX_API_KEY` | Every package validates on production from its files, and its contract snapshot is current |
| `make check-recipes` | Nothing | Every directory under a recipe's `generated/` has a sidecar naming an address pinned to a release tag and a target its language reads, and every page snippet's tree a sidecar naming what its types come from and a target its code reads, the recipe's code calls that same address as a whole string literal, every Python recipe script declares `pipelex-sdk`, every TypeScript recipe's `package.json` depends on `@pipelex/sdk` and has its `codegen:check` script check each of its trees, every address a recipe's README, shell script or JSON file names with a tag carries a release tag, and every recipe's shell script parses under `sh -n` |
| `make check-codegen` | The network, once, to install `pipelex-sdk` into the script's environment | Every recipe's and page snippet's generated types still match their `codegen.lock`: no file edited, missing or left over |
| `make check-recipe-types` | The network, to install each recipe's and snippet's dependencies, Node.js 22 with npm, and shellcheck | Every Python recipe script and page snippet type-checks in strict mode, in its own environment, with the method's generated types, every TypeScript recipe package passes its codegen gate and `tsc --noEmit`, the page snippets' package passes `tsc --noEmit`, and every recipe's shell script passes shellcheck. Where shellcheck is not installed, the check says so and goes on; in CI, whose runner image carries it, its absence fails the check |
| `make check-addresses` | `PIPELEX_API_KEY` | Every page's address validates on production at the page's tag, as a reader running it would reach it, and so does every address a recipe names, in its sidecars or in its README, shell scripts and JSON files, and every library method the front page lists. A page's method the tag does not carry yet, or a tag not pushed yet, is reported as not released rather than failed: production answers the first with a 404 whose problem type is `method-package-not-found-error`, and the second with a `MethodFetchError` saying the tag names no git tag. Any other refusal fails, and so does a recipe's or a listed library method's address that does not resolve, released or not, since a recipe runs its address as it names it, and a code recipe's types were generated from it |
| `make check-codegen-live` | `PIPELEX_API_KEY` | Every recipe's `codegen.lock` records the crate fingerprint its address resolves to today, and every page snippet's the one its package's `.mthds` files make today, as `POST /v1/codegen` reports it |
| `make refresh-library` | The network | Rewrites `library.json` from the library's tarball at the tag `cookbook.toml` pins |
| `make refresh` | `PIPELEX_API_KEY` | Rewrites the library's snapshot, then every contract snapshot from production, renders, then rewrites every recipe's and page snippet's generated types from production |

`make check-cookbook` runs every check that needs no key, and is what the `Methods check` workflow runs on every pull request. `make agent-check` runs `check-render`, `check-lockstep`, `check-recipes` and `check-codegen` after the linters. The checks that call production, `check-methods`, `check-addresses` and `check-codegen-live`, are grouped under `make check-hosted`: CI holds no API key, so their author runs them by hand before each pull request, and the release play runs them at each release. After a release, `make check-addresses` is also what proves it: once the tag exists, every method must validate at it. None of them spends inference; running a method is a separate, deliberate act.

The tooling calls `POST /v1/validate` with `httpx`. The recipes' codegen, which needs `pipelex-sdk`, runs in an environment of its own, so that every generated tree is written and checked with the exact SDK release `scripts/sdk/recipe_codegen.py` pins.
