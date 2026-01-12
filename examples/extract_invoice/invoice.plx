domain = "invoice_extraction"

[concept]
Invoice = "Invoice information extracted from text"
InvoiceDetails = "The category of the invoice"

[pipe]
[pipe.process_invoice]
type = "PipeSequence"
description = "Process relevant information from an invoice"
inputs = { document = "PDF" }
output = "Invoice[]"
steps = [
    { pipe = "extract_page_contents_and_views_from_pdf", result = "invoice_pages" },
    { pipe = "extract_invoice", batch_over = "invoice_pages", batch_as = "invoice_page", result = "invoice" },
]

[pipe.extract_invoice]
type = "PipeSequence"
description = "Extract invoice information from an invoice text transcript"
inputs = { invoice_page = "Page" }
output = "Invoice"
steps = [
    { pipe = "analyze_invoice", result = "invoice_details" },
    { pipe = "extract_invoice_data", result = "invoice" },
]

[pipe.analyze_invoice]
type = "PipeLLM"
description = "Analyze the invoice"
inputs = { invoice_page = "Page" }
output = "InvoiceDetails"
prompt = """
Analyze this invoice:

@invoice_page.text_and_images.text.text
"""

[pipe.extract_invoice_data]
type = "PipeLLM"
description = "Extract invoice information from an invoice text transcript"
inputs = { "invoice_page.page_view" = "Image", invoice_details = "InvoiceDetails", invoice_page = "Page" }
output = "Invoice"
model = "llm_for_img_to_text"
prompt = """
Extract invoice information from this invoice:

The category of this invoice is: $invoice_details.category.

{{ invoice_page.text_and_images.text.text|tag("ocr_extacted_text") }}

Page view: $invoice_page.page_view
"""

