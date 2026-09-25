# /// script
# requires-python = ">=3.11"
# dependencies = ["pipelex-sdk==0.12.0"]
# ///
"""Extract every invoice a CSV lists, a few at a time, and write what each one says to a results CSV.

Each row of the input CSV names an invoice by URL, in its `invoice_url` column. The script runs the Pipelex method
library's invoice extraction on every row by its address, keeps at most `--concurrency` runs going at once, and writes
one row per invoice found: the vendor, the date, the totals and the VAT, beside the URL it came from and the run's id.
A row whose run fails gets its error in the results instead of stopping the batch.

    uv run batch.py invoices.csv --output results.csv --concurrency 4

`PIPELEX_API_KEY` must be set; each invoice is one run on the hosted API and spends credit.
"""

import argparse
import asyncio
import csv
import sys
from pathlib import Path
from typing import Any

import httpx
from mthds.protocol.exceptions import PipelineRequestError
from pipelex_sdk.client import PipelexAPIClient
from pydantic import BaseModel, TypeAdapter

from generated.invoice_extraction.models import Invoice

METHOD_REF = "github.com/Pipelex/methods/invoice_extraction@v0.1.1"
URL_COLUMN = "invoice_url"
OUTPUT_COLUMNS = ["invoice_url", "vendor", "invoice_number", "issue_date", "amount_excl_tax", "vat_amount", "amount_incl_tax", "run_id", "error"]


class InvoiceList(BaseModel):
    """The envelope `{"items": [...]}` the SDK documents for a list output."""

    items: list[Invoice]


# The method returns a list of invoices, one per bill or receipt the document holds. The SDK documents a list output as
# the envelope {"items": [...]}, while the hosted API answers a bare list today, so both shapes are read.
INVOICES = TypeAdapter[list[Invoice] | InvoiceList](list[Invoice] | InvoiceList)


async def extract_one(client: PipelexAPIClient, semaphore: asyncio.Semaphore, url: str) -> list[dict[str, Any]]:
    """Run the method on one invoice and return its rows: one per invoice found, or one carrying the error."""
    async with semaphore:
        print(f"… {url}", file=sys.stderr)
        try:
            results = await client.start_and_wait(method_ref=METHOD_REF, inputs={"document": {"url": url}})
        except (PipelineRequestError, httpx.HTTPStatusError) as exc:
            print(f"✗ {url}: {exc}", file=sys.stderr)
            return [{"invoice_url": url, "error": str(exc)}]
    parsed = INVOICES.validate_python(results.main_stuff)
    invoices = parsed.items if isinstance(parsed, InvoiceList) else parsed
    print(f"✓ {url}: {len(invoices)} invoice(s), run {results.pipeline_run_id}", file=sys.stderr)
    return [
        {
            "invoice_url": url,
            "vendor": invoice.vendor,
            "invoice_number": invoice.invoice_number,
            "issue_date": invoice.issue_date,
            "amount_excl_tax": invoice.amount_excl_tax,
            "vat_amount": invoice.vat_amount,
            "amount_incl_tax": invoice.amount_incl_tax,
            "run_id": results.pipeline_run_id,
        }
        for invoice in invoices
    ]


async def extract_all(urls: list[str], *, concurrency: int) -> list[dict[str, Any]]:
    """Run the method on every URL through one client, at most `concurrency` runs at a time, keeping the CSV's order."""
    semaphore = asyncio.Semaphore(concurrency)
    async with PipelexAPIClient() as client:
        per_url = await asyncio.gather(*(extract_one(client, semaphore, url) for url in urls))
    return [row for rows in per_url for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract every invoice a CSV lists, and write what each one says to a results CSV.")
    parser.add_argument("input", type=Path, nargs="?", default=Path(__file__).parent / "invoices.csv", help="A CSV with an invoice_url column")
    parser.add_argument("--output", type=Path, default=Path("results.csv"), help="Where to write the results (default: results.csv)")
    parser.add_argument("--concurrency", type=int, default=4, help="How many runs to keep going at once (default: 4)")
    arguments = parser.parse_args()

    with arguments.input.open(newline="", encoding="utf-8") as input_file:
        urls = [row[URL_COLUMN].strip() for row in csv.DictReader(input_file) if row.get(URL_COLUMN, "").strip()]
    rows = asyncio.run(extract_all(urls, concurrency=arguments.concurrency))

    with arguments.output.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    failed = sum(1 for row in rows if row.get("error"))
    print(f"{arguments.output}: {len(rows) - failed} invoice(s) from {len(urls)} document(s), {failed} failed")


if __name__ == "__main__":
    main()
