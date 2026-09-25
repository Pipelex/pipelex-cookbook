# A local file sent to a method through an upload grant

A method reads its documents and images from links the hosted API can fetch, and a file on your machine or in your visitor's browser has none. This recipe sends a local image of a Gantt chart to Pipelex storage through an upload grant, then runs the cookbook's [Gantt chart extraction](../../../../methods/extract_gantt/) on it and prints every task and milestone it reads.

It shows the three steps of an upload:

- **The grant.** `requestUploadGrant` asks the hosted API for a one-time place to put one file of a given name, type and size. It is the only step that needs the API key.
- **The upload.** `uploadWithGrant` sends the bytes straight to storage with the grant, not through the API. In a web app, the server asks for the grant and the browser does this step, with `uploadWithGrant` from `@pipelex/sdk/upload`, the SDK's browser-safe entry, so the file never passes through your server and the key never reaches the browser.
- **The run.** The upload answers with a storage uri, `pipelex-storage://…`, which the method reads as the image's `url`.

## What it needs

- [Node.js](https://nodejs.org/) 22.12 or later.
- A Pipelex API key in `PIPELEX_API_KEY`, from [app.pipelex.com](https://app.pipelex.com). Each chart is one run on the hosted API and spends credit.

## Run it

```bash
npm install
export PIPELEX_API_KEY=…
npm run --silent extract -- ../../../../assets/extract_gantt/gantt_tree_house.png
```

The image is the cookbook's sample chart, the plan of a tree house; any PNG, JPEG or WebP image of a Gantt chart works.

## What you get

One line per task with its start and end dates, then one line per milestone with its date:

```text
2025-09-01 → 2025-09-08  Planning & Design
2025-09-05 → 2025-09-10  Resource Gathering
…
◆ 2025-09-08  Blueprint
◆ 2025-10-11  Celebration
```

On the sample chart, that is 12 tasks and 5 milestones. The storage uri and the run's id go to stderr.

## How it is built

- `extract.ts` calls the method by its address, `github.com/Pipelex/pipelex-cookbook/extract_gantt@v0.18.0`, pinned to a release tag so the method never changes under the types, and reads the chart through `parseGanttChart`, generated from the method's output.
- `generated/extract_gantt/` holds the method's types: `types.ts` and `binder.ts`, generated from the method at that tag, and `codegen.lock`, which vouches for them. `sources.json` records the address and the target they come from. Never edit them by hand: in the cookbook, `make refresh` regenerates them, and in your own project `/pipelex-integrate` does. `npm run codegen:check` checks them against their lock offline, with `scripts/codegen-check.mjs`, copied as it is from the `pipelex-integrate` skill.
- When the file is already where the key is, `client.uploadFile(path)` uploads it in one call. The grant is for a file that is somewhere else than the key, such as in a visitor's browser, which is why the recipe spells out its steps. The grant itself is a short-lived bearer capability for one upload, so the script never prints it.
