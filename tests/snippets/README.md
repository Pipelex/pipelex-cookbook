# Page snippets

Every method page, `methods/<name>/README.md`, shows how to call its method from TypeScript and from Python. `make render` writes those two snippets here as files, from the same templates the page includes them from, so that what a page shows is what CI type-checks:

- `<name>/typescript/snippet.ts` is the page's TypeScript snippet, under a comment saying where it comes from.
- `<name>/python/snippet.py` is the page's Python snippet, opening with the inline dependencies `uv run` reads, then the same comment.

**Everything under `<name>/` is generated.** Never edit it by hand: change the method's package, `cookbook.toml` or `templates/snippets/`, then run `make render`. `make check-render` fails when a file here differs from a fresh render, and when a directory here belongs to no method under `methods/`, which `make render` never deletes.

The rest of this directory is written by hand: this README, and the one TypeScript package every TypeScript snippet compiles in, `package.json` with its `package-lock.json` and `tsconfig.json`. It pins `@pipelex/sdk` exactly, as the TypeScript recipes under `recipes/code/typescript/` do, and moves with them.

## How they are checked

`make check-recipe-types`, which `make check-cookbook` and CI run, type-checks the snippets beside the recipes:

- each `snippet.py` with pyright in strict mode, under `recipes/pyrightconfig.json`, in the environment its own inline dependencies describe;
- the package with `npm ci` from its lock, then `tsc --noEmit` over every `<name>/typescript/` directory.

The Python SDK types an input as a string, a list of strings, a content object or a list of them, or a dict. A sample passing a list of plain objects, such as several documents each given by its URL, is refused by that type although the hosted API reads it, so its `snippet.py` says so in a comment and leaves argument types unchecked until the type admits one.

## Running one

A snippet runs on the hosted API with your `PIPELEX_API_KEY` set, and each run spends credit. From the repository's root:

```bash
uv run tests/snippets/<name>/python/snippet.py
```
