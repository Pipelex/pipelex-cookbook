# A local file sent to a method through an upload grant

A method reads its documents and images from links the hosted API can fetch, and a file on your machine or in your visitor's browser has none. This recipe sends a French energy performance diagnostic (DPE) from your disk to Pipelex storage through an upload grant, then runs the cookbook's [DPE extraction](https://github.com/Pipelex/pipelex-cookbook/tree/v0.20.0/methods/extract_dpe) on it and prints the record it reads.

It shows the steps of an upload:

- **The grant.** `requestUploadGrant` asks the hosted API for a one-time place to put one file of a given name, type and size. It is the only step of the upload itself that needs the API key, and the run that follows needs it too.
- **The upload.** `uploadWithGrant` sends the bytes straight to storage with the grant, not through the API. In a web app, the server asks for the grant and the browser does this step, with `uploadWithGrant` from `@pipelex/sdk/upload`, the SDK's browser-safe entry, so the file never passes through your server and the key never reaches the browser.
- **The run.** The upload answers with a storage uri, `pipelex-storage://…`, which the method reads as the document's `url`.

## What it needs

- [Node.js](https://nodejs.org/) 22.12 or later.
- A Pipelex API key in `PIPELEX_API_KEY`, from [app.pipelex.com](https://app.pipelex.com). Each chart is one run on the hosted API and spends credit.

## Run it

```bash
npm install
export PIPELEX_API_KEY=…
npm run --silent extract -- ../../../../assets/extract_dpe/synthetic_dpe.pdf
```

The document is the cookbook's sample DPE, a fictional one made for the example; any DPE as a PDF works.

## What you get

The record the method reads, one field per line:

```text
Address       18 rue des Exemples, 69003 LYON 3EME, Étage 3 ; Porte gauche ; N° de lot : 27
DPE number    2669E0000000X
Valid         2026-06-18 → 2036-06-17
Energy class  F, 342 kWh/m²/year
CO₂ class     E, 61 kg/m²/year
Energy costs  1380 to 1870 € a year, at the prices of 2025-01-01
Letting       Rent frozen; no new or renewed lease from 1 January 2028
```

These are the figures printed on the sample diagnostic, whose dwelling and people are invented, and the last line is what its class means for letting the dwelling. The storage uri and the run's id go to stderr.

## How it is built

- `extract.ts` calls the method by its address, `github.com/Pipelex/pipelex-cookbook/extract_dpe@v0.20.0`, pinned to a release tag so the method never changes under the types, and reads the record through `parseDpeRecord`, generated from the method's output.
- `generated/extract_dpe/` holds the method's types: `types.ts` and `binder.ts`, generated from the method at that tag, and `codegen.lock`, which vouches for them. `sources.json` records the address and the target they come from. Never edit them by hand: in the cookbook, `make refresh` regenerates them, and in your own project `/pipelex-integrate` does. `npm run codegen:check` checks them against their lock offline, with `scripts/codegen-check.mjs`, copied as it is from the `pipelex-integrate` skill.
- When the file is already where the key is, `client.uploadFile(path)` uploads it in one call. The grant is for a file that is somewhere else than the key, such as in a visitor's browser, which is why the recipe spells out its steps. The grant itself is a short-lived bearer capability for one upload, so the script never prints it.
