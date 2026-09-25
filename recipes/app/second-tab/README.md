# A second method as a second tab

An app made from one method grows by a command. `make add-method` takes a second method by its address and writes everything the app needs around it, its form, its Server Actions and its generated types, then registers it, and the page turns into tabs, one per method. This recipe adds the [invoice extraction](https://github.com/Pipelex/methods/tree/v0.1.1/methods/invoice_extraction) method of the Pipelex method library to the DPE app the [deployed-app recipe](../deployed-app/) makes, so one app reads both an energy diagnostic and an invoice.

It shows how an app on published methods changes:

- **A method is one command and one commit.** `make add-method` writes nothing until it has fetched and derived everything, then writes one slice per method and a single registry entry, and refuses rather than overwrite a method already there.
- **Each tab keeps its own address and tag.** The second method is pinned to `github.com/Pipelex/methods/invoice_extraction@v0.1.1`, the method library's release, independently of the first, which stays at the cookbook's `v0.18.0`.
- **Moving to another release is one edit.** Change the tag in the method's `method.json` and run `npm run codegen`: the regenerated types show what the new release changed, and `make check` fails until they are regenerated.

## What it needs

- The app from the [deployed-app recipe](../deployed-app/), or any app made from the [`webapp-js`](https://github.com/Pipelex/pipelex-method-apps/tree/main/webapp-js#readme) template. Commit what it holds first, so the new method arrives as a diff of its own.
- A Pipelex API key, from [app.pipelex.com](https://app.pipelex.com), in `PIPELEX_API_KEY` or in the app's `.env.local`: adding a method reads its contract from the API, which spends no credit.
- Credit on your Pipelex account for each run from the form.

## Run it

```bash
cd dpe-app
make add-method METHOD=github.com/Pipelex/methods/invoice_extraction@v0.1.1
make all
make serve
```

`make add-method` writes the method's slice and says what it wrote, `make all` checks, tests and builds the app with it and needs no key, and `make serve` prints the page's URL. Open the "Invoice extraction" tab, drop the [sample invoice](https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/v0.18.0/assets/extract_proof_of_purchase/restaurant_invoice.pdf) on its form and run it.

`DRY_RUN=1` prints the plan and writes nothing, `LABEL=…` names the tab, and `NAME=…` chooses the slug every file is named after.

## What you get

`make add-method` says which pipe it wires, what the method returns and what it wrote:

```text
add-method: method_ref github.com/Pipelex/methods/invoice_extraction@v0.1.1, via https://api.pipelex.com
  pipe:   invoice_extraction.process_invoice
  output: invoice_extraction.Invoice (plural — a list of the concept)
  files:  document
  entry:  "Invoice extraction" (id invoice-extraction)

Wrote:
  methods/invoice-extraction/method.json
  src/generated/invoice-extraction/  (types.ts, binder.ts, contracts.ts, codegen.lock, sources.json)
  src/types/invoiceExtractionPipeline.ts
  src/types/invoiceExtractionUploads.ts
  src/actions/runInvoiceExtractionPipeline.ts
  src/actions/runInvoiceExtractionPipeline.test.ts
  src/components/InvoiceExtractionForm.tsx
  src/methods.ts  (one import, one entry)
```

The page now has two tabs, "Extract DPE" and "Invoice extraction". The page's title is still the first method's, "Extract DPE", since the app's title and description live in `src/site.ts`, which adding a method leaves alone: edit them there. On the sample invoice, the second tab's run took about half a minute, and its result view is a table with one row per invoice the document holds:

| Invoice id | Issue date | Amount incl tax | Amount excl tax | Vat amount |
|---|---|---|---|---|
| 914946 | 2025-03-09 | 9.96 | 8.88 | 0.81 |

Below the table come the run's id, `run_…`, and its "Usage and cost" disclosure, as on the first tab.

## How it is built

The recipe is one command of the [`webapp-js`](https://github.com/Pipelex/pipelex-method-apps/tree/main/webapp-js#readme) template, so it carries no code of its own. The template's [`make add-method` guide](https://github.com/Pipelex/pipelex-method-apps/blob/main/webapp-js/docs/add-method.md) is the reference.

- **The slice.** `methods/invoice-extraction/method.json` names the address, and `src/generated/invoice-extraction/` holds the types generated from the method at that tag, with the lock that vouches for them. `src/types/` narrows the output to those types, `src/actions/` holds the Server Actions that start the run and poll it, with a test, and `src/components/InvoiceExtractionForm.tsx` is the form and the result view, both rendered from the method's contract. It is also where you replace either with your own.
- **The registry.** `src/methods.ts` gains one import and one entry, and the page renders one tab per entry. Nothing else in the app names a method, so removing one is deleting its slice and its entry in one commit, as the guide's "Removing a method" lists them.
- **The run follows the manifest.** The Server Action sends the address it reads from `method.json`, so moving the tag moves the run with it, and `npm run codegen` moves the types.
- **Any method works the same way.** `METHOD` also takes a directory of `.mthds` files, which are copied into `methods/<name>/`, or a method saved in your organization's catalog by its `mt_…` id.
