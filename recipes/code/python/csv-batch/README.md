# A method over every row of a CSV

A spreadsheet lists invoices by link, and you want one row per invoice with its vendor, date, totals and VAT. This recipe runs the [invoice extraction method](https://github.com/Pipelex/methods/tree/v0.1.1/methods/invoice_extraction) of the Pipelex method library on every row, a few runs at a time, and writes what each invoice says to a results CSV.

It shows three things you need as soon as a method runs on more than one input:

- **Bounded concurrency.** One `PipelexAPIClient` serves every row, and an `asyncio.Semaphore` keeps at most `--concurrency` runs going at once, so a long CSV neither waits on each run in turn nor starts hundreds at once.
- **A list output, typed.** The method returns a list of invoices, one per bill or receipt the document holds. The script validates it into the `Invoice` model generated from the method, so every field it writes is typed.
- **Failures as rows.** A run that fails, a network failure, or an output the generated types refuse puts its error in the results, beside the URL it came from, and the batch carries on. A document in which the method finds no invoice gets a row saying so, so every URL of the input appears in the output.

## What it needs

- [uv](https://docs.astral.sh/uv/), which reads the script's dependencies from its first lines and installs them.
- A Pipelex API key in `PIPELEX_API_KEY`, from [app.pipelex.com](https://app.pipelex.com). Each invoice is one run on the hosted API and spends credit.

## Run it

```bash
export PIPELEX_API_KEY=…
uv run batch.py invoices.csv --output results.csv --concurrency 4
```

`invoices.csv` holds two sample invoices from the cookbook's `assets/`, linked at the release tag `v0.18.0`. Point the script at your own CSV: it reads the `invoice_url` column, and each URL must be one the hosted API can fetch, such as a public link or a presigned URL.

## What you get

`results.csv`, with one row per invoice found:

| Column | What it holds |
|---|---|
| `invoice_url` | The document the row comes from |
| `vendor`, `invoice_number`, `issue_date` | Who billed, the invoice's number and its date |
| `amount_excl_tax`, `vat_amount`, `amount_incl_tax` | The totals, as numbers |
| `run_id` | The run that read it, to find it again in your Pipelex account |
| `error` | Why no invoice came from the document: the run's error, or that the method found none |

On the two sample invoices, the rows read like this (the run ids trimmed):

```csv
invoice_url,vendor,invoice_number,issue_date,amount_excl_tax,vat_amount,amount_incl_tax,run_id,error
…/restaurant_invoice.pdf,JFK 5B Food Hall,JFK5BFDH6707,2025-03-09,8.88,0.81,9.96,run_…,
…/invoice_1.pdf,Johnny Rockets,2080,2025-03-11,27.94,2.34,30.28,run_…,
```

Progress goes to the terminal as each run starts and ends, and the last line counts the invoices written and the documents that gave none.

## How it is built

- `batch.py` calls the method by its address, `github.com/Pipelex/methods/invoice_extraction@v0.1.1`, pinned to a release tag so the method never changes under the types.
- `generated/invoice_extraction/` holds those types: `models.py`, generated from the method at that tag, and `codegen.lock`, which vouches for it. `sources.json` records the address and the target they come from. Never edit them by hand: in the cookbook, `make refresh` regenerates them, and in your own project `/pipelex-integrate` does.
- To run another method over a CSV, change the address, generate its types, and change the columns the script reads and writes.
