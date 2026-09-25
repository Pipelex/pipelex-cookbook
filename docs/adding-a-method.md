# Adding a method

A cookbook method is a package that anyone can run by address on the hosted API, with a sample, an answer key, and a generated page. [README.md](README.md) explains each part; this is the order to do it in.

## 1. Make the package

Create `methods/<name>/`, where `<name>` is snake_case and becomes the last part of the method's address, `github.com/Pipelex/pipelex-cookbook/<name>@<tag>`.

- **The bundles**, as `.mthds` files. They must meet the hosted bar: declare types as MTHDS concepts (`[concept.X.structure]` tables), never as Python structure classes, and call only the package's own pipes, since hosted execution does not yet serve a call into another package. When a method needs a pipe from the library, copy it into the package.
- **`METHODS.toml`**, modelled on an existing one:

  ```toml
  [package]
  name = "<name>"
  display_name = "<Title Case Name>"
  address = "github.com/Pipelex/pipelex-cookbook"
  version = "<the version in pyproject.toml>"
  description = "<one sentence on what the method does>"
  authors = ["Evotis S.A.S"]
  license = "MIT"
  mthds_version = ">=1.0.0"
  main_pipe = "<the entry pipe's code>"

  [exports.<domain>]
  pipes = ["<the entry pipe's code>"]
  ```

- **The sample**, as files under `assets/<name>/`, and **`inputs.json`** naming each file by its raw URL on `main`: `https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/main/assets/<name>/<file>`. The URL answers once a release brings the file to `main`; until then `make check-links` reports it as not published, which is expected. A sample already under `assets/` keeps its place, and a public file hosted elsewhere keeps its own URL, which must answer. An input taking several files lists one `{"url": …}` per file. Text inputs are written inline.

## 2. Write the answer key, before the first run

`methods/<name>/key.md` lists what a right answer on the sample holds, in the format of the Pipelex lab skill (`/pipelex-lab`): `# Key: <case>`, an `Inputs:` line, then `## Planted facts`, `## Must`, `## Must not`, `## Also acceptable` and `## Pass bar`, every line labelled (`F1.`, `M1.`, `N1.`, `A1.`). One checkable fact per line, naming the output field it reads.

Write it from the sample, before the method runs on it, so that the run is scored against it rather than the key fitted to the run. The page shows the `## Must` lines as "What you get", on their own, so each Must line states its facts in full rather than citing a planted fact.

## 3. Prove it on production

With `PIPELEX_API_KEY` set:

1. `make refresh` validates every package on production from its files and writes each `contract.json`. A package that is not valid prints the verdict and keeps its old snapshot.
2. Run the method once on its sample, from its files, for instance with `/pipelex-run` on the package directory or through the Pipelex MCP. A run spends inference, so it is started by hand, once.
3. Score the output against the key. When the pass bar is not met, fix the method, not the key, and run it again.

## 4. Give it its page

1. Add an entry to `cookbook.toml` under `[methods.<name>]` with the title, the pitch, the sample's link text, the chatbot sentence and the "Make it yours" change. Every field is optional.
2. `make render` writes `methods/<name>/README.md`, and the page's TypeScript and Python snippets as files under `tests/snippets/<name>/`. Read the page as a reader would, and commit the snippet files with it.

## 5. Check and open the pull request

1. `make agent-check` and `make agent-test`: the linters, the page freshness, the lockstep versions and the tests.
2. `make check-recipe-types`, which type-checks the page's snippet files against the SDK, each in its own environment.
3. `make check-hosted`, by hand, since CI holds no key.
4. An entry in `CHANGELOG.md` under `## [Unreleased]`.

The method resolves by address once the next release brings it to `main`; the release re-renders every page at its tag.
