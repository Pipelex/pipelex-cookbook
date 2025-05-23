# Sample Pipelines to show off Pipelex capabilities

(🏗️ this area is still under construction)

The scripts in this folder demonstrate more advanced Pipelex pipelines. They
rely on helper functions in `cookbook/utils` and write their results to the
`results/samples/` directory.

- `expense_report.py` processes invoices and an expense report to extract
  structured information.
- `extract_gantt.py` extracts a gantt chart from an image.
- `extract_table.py` extracts an HTML table from an image screenshot.
- `pdf_1_simple_ocr.py` demonstrates basic OCR capabilities on PDF documents,
  extracting text and images from each page.
- `pdf_2_power_extractor.py` shows advanced PDF processing with the power extractor pipeline,
which can handle complex documents with text embedded in images, thanks to a second step using a VLM (Visual Language Model).

Run any sample from the repository root, for example:

```bash
python cookbook/samples/extract_table.py
```
