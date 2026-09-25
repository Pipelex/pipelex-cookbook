# Page snippets

Every method page, `methods/<name>/README.md`, shows how to call its method from TypeScript and from Python. `make render` writes those two snippets here as files, from the same templates the page includes them from, so that what a page shows is what CI type-checks:

- `<name>/typescript/snippet.ts` is the page's TypeScript snippet, under a comment saying where it comes from.
- `<name>/python/snippet.py` is the page's Python snippet, opening with the inline dependencies `uv run` reads, then the same comment.

Below the page's snippet, each file reads the run's output through the method's generated types, which the page does not show: the TypeScript file parses `result.main_stuff` with the binder's `parse…` function for the output concept, and the Python file defines `read_output`, which validates it as that concept's model. The concept is the one the page's "Returns" line names, and a list output is read both as a bare list and as the `{"items": [...]}` envelope. So a type checker fails when the page names a concept the method's types no longer hold, and loading the cookbook fails when that concept is not the main pipe's declared output, while a reader still copies a snippet that needs no generated types.

The types sit beside each file, in `<name>/typescript/generated/<name>/` and `<name>/python/generated/<name>/`, laid out as a code recipe's under `recipes/`. Their `sources.json` is written by `make render` and names the `.mthds` files of the method's package, by their paths from the repository root, and `make refresh` generates the rest from those files: `types.ts`, `binder.ts` and `codegen.lock` in TypeScript, `models.py`, `codegen.lock` and the two `__init__.py` files in Python. The types come from the files rather than from the page's address because a page names the last release's tag, which does not hold a method added since.

**Everything under `<name>/` is generated.** Never edit it by hand: change the method's package, `cookbook.toml` or `templates/snippets/`, then run `make render`, or `make refresh` when a bundle changed. `make check-render` fails when a snippet file or a sidecar here differs from a fresh render, and when a directory here belongs to no method under `methods/`, which `make render` never deletes. `make check-codegen` fails when a generated file no longer matches its lock, and `make check-codegen-live`, with a key, when the lock no longer records what the package's files make.

The rest of this directory is written by hand: this README; the one TypeScript package every TypeScript snippet compiles in, `package.json` with its `package-lock.json` and `tsconfig.json`, which pins `@pipelex/sdk` exactly, as the TypeScript recipes under `recipes/code/typescript/` do, and moves with them; and `pyrightconfig.json`, which extends `recipes/pyrightconfig.json`.

## How they are checked

`make check-recipe-types`, which `make check-cookbook` and CI run, type-checks the snippets beside the recipes:

- each `snippet.py` with pyright in strict mode, in the environment its own inline dependencies describe, under `pyrightconfig.json` here, whose root lets pyright resolve `generated.<name>` beside the file, which it only does for a file under the configuration's root;
- the package with `npm ci` from its lock, then `tsc --noEmit` over every `<name>/typescript/` directory, generated types included.

The package runs no `codegen:check` script of its own, as a TypeScript recipe does: `make check-codegen` checks every tree here against its lock already, and the gate's other half, which compares the source hashes a sidecar records with the bundle, has nothing to compare, since these sidecars record none.

The Python SDK types an input as a string, a list of strings, a content object or a list of them, or a dict. A sample passing a list of plain objects, such as several documents each given by its URL, is refused by that type although the hosted API reads it, so its `snippet.py` says so in a comment and leaves argument types unchecked until the type admits one.

## Running one

A snippet runs on the hosted API with your `PIPELEX_API_KEY` set, and each run spends credit. From the repository's root:

```bash
uv run tests/snippets/<name>/python/snippet.py
```
