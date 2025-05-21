# Sample Pipelines

The scripts in this folder demonstrate more advanced Pipelex pipelines. They
rely on helper functions in `cookbook/utils` and write their results to the
`results/samples/` directory.

- `expense_report.py` processes invoices and an expense report to extract
  structured information.
- `extract_gantt.py` extracts a gantt chart from an image.
- `extract_table.py` extracts an HTML table from an image screenshot.

Run any sample from the repository root, for example:

```bash
python cookbook/samples/extract_table.py
```
