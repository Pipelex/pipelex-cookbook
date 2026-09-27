# A Next.js form whose server action runs a method

Your site needs a form that makes something for its visitor: here, a batch of realistic test records, from a description of what they are for and how many to make. This recipe is a Next.js app with one page whose server action runs the cookbook's [synthetic data](https://github.com/Pipelex/pipelex-cookbook/tree/v0.20.0/methods/gen_synthetic_data) method by its address, and renders the records it returns as a table.

It shows how a method becomes part of a web app:

- **The key stays on the server.** The server action is the only code that calls the hosted API, through one `PipelexApiClient` for the whole server process, which reads `PIPELEX_API_KEY` from the server's environment. The browser sends the form and gets the records back, and never sees the key.
- **The method's types on both sides.** The action sends the form as the method's own inputs, a `DataDescription` and a `RecordCount`, through `serializeDataDescription` and `serializeRecordCount`, generated from them, and reads the answer through `parseDataRecord`, generated from its output, so the page renders typed records. The method takes its count as a plain number and bounds nothing, so the action refuses, before spending a run, a count that is not a whole number from 1 to 20, and a description longer than four thousand characters.
- **Failures as messages.** A form the action refuses, a run that fails, or an answer the types do not accept comes back to the page as a message saying why, instead of a server error.

## What it needs

- [Node.js](https://nodejs.org/) 22.12 or later.
- A Pipelex API key in `PIPELEX_API_KEY`, from [app.pipelex.com](https://app.pipelex.com). Each batch is one run on the hosted API and spends credit.

## Run it

```bash
npm install
export PIPELEX_API_KEY=…
npm run dev
```

Then open http://127.0.0.1:3000, and generate records with the form's sample values or your own. The sample is the method's own: test tickets for the triage of an online shop's customer service, the shop and its customers invented, ten of them.

## What you get

The records under the form, as a table with the id of the run that wrote them: a first column saying the case each record was written to cover, then one column per field the description names, in its order. On the sample values, the run answered in about forty seconds with ten tickets, in French and in English, by email and through the contact form, some two lines long and annoyed, some long and polite, a few with typos, one asking two things at once and one with no order number. Every queue the description names has at least one ticket, and each ticket's priority follows its rules: the smoking toaster, the blender smelling of burning and the card charged twice are urgent, the kettle a week late and the overdue refund are high, and the rest are normal.

## Before you deploy it

The app has no authentication of its own, and every batch it generates is a run on your key's credit. Run as above, `npm run dev` and `npm start` listen on `127.0.0.1` only, so nothing but your own machine reaches the form. Deployed, anyone who reaches the page spends your credit. A server action is also a public endpoint that anyone can post to directly, without the page, so the guard belongs in the action itself: check your site's own session at its top, and put a rate limit in front of it, before it faces a network. The action already bounds the count and the description's length, in `lib/limits.ts`.

## How it is built

- `app/actions.ts` is the server action. It calls the method by its address, `github.com/Pipelex/pipelex-cookbook/gen_synthetic_data@v0.20.0`, pinned to a release tag so the method never changes under the types, and waits for the run with `startAndWaitForResult`. The method returns a list, which the action reads both as a bare list and as the envelope `{"items": [...]}` that the SDK documents.
- `app/page.tsx` is the form, a client component that calls the action through React's `useActionState`. React resets a form once its action has run, so the action sends back what the visitor typed with every answer, and the form shows it again. `lib/pipelex.ts` holds the client, and only server code imports it; `lib/limits.ts` holds the bounds the page and the action share, since a file of server actions exports nothing but its actions.
- `generated/gen_synthetic_data/` holds the method's types: `types.ts` and `binder.ts`, generated from the method at that tag, and `codegen.lock`, which vouches for them. `sources.json` records the address and the target they come from. Never edit them by hand: in the cookbook, `make refresh` regenerates them, and in your own project `/pipelex-integrate` does. `npm run codegen:check` checks them against their lock offline, with `scripts/codegen-check.mjs`, copied as it is from the `pipelex-integrate` skill.
- The records come back while the visitor waits, which a server action can do. A method that runs for many minutes belongs in the [durable run](../durable-run/) pattern instead: start the run in the action, return its id, and let the page ask for the result.
