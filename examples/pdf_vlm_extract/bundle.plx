domain = "pdf_vlm_extract"
description = "Extract from PDF using OCR, then correct with VLM"
main_pipe = "extract_and_correct"

[concept.OCRCorrection]
description = "A single correction to apply to OCR text"

[concept.OCRCorrection.structure]
ocr_text = { type = "text", description = "The text as extracted by OCR (what we have)" }
expected_text = { type = "text", description = "The text as it should be (what it is supposed to be)" }
correction = { type = "text", description = "Description of the correction to apply" }
location = { type = "text", description = "Where in the document this correction applies" }

[concept.OCRAnalysis]
description = "Analysis of OCR errors and missing parts identified by comparing with the original image"

[concept.OCRAnalysis.structure]
missing_parts = { type = "list", item_type = "text", description = "Text that was completely missed by OCR" }
corrections = { type = "list", item_type = "concept", item_concept_ref = "pdf_vlm_extract.OCRCorrection", description = "List of corrections to apply" }
overall_quality = { type = "text", description = "Assessment of OCR quality", choices = ["good", "moderate", "poor"] }

[pipe]
[pipe.extract_and_correct]
type = "PipeSequence"
description = "Extract PDF pages then use VLM to correct OCR errors"
inputs = { document = "Document" }
output = "Text[]"
steps = [
    { pipe = "extract_page_contents_and_views_from_pdf", result = "pages" },
    { pipe = "analyze_and_correct_page", batch_over = "pages", batch_as = "page", result = "corrected_texts" },
]

[pipe.analyze_and_correct_page]
type = "PipeSequence"
description = "Analyze OCR errors then apply corrections for a single page"
inputs = { "page.page_view" = "Image", page = "Page" }
output = "Text"
steps = [
    { pipe = "identify_ocr_issues", result = "ocr_analysis" },
    { pipe = "apply_corrections", result = "corrected_text" },
]

[pipe.identify_ocr_issues]
type = "PipeLLM"
description = "Identify OCR errors and missing parts by comparing with the original image"
inputs = { "page.page_view" = "Image", page = "Page" }
output = "OCRAnalysis"
model = "$vision"
system_prompt = "You are an OCR quality analyst. Your job is to compare OCR-extracted text with the original document image and identify ONLY actual discrepancies."
prompt = """
You are given a page view (screenshot) of a document: $page.page_view

You are also given the text that was extracted by OCR:
{{ page.text_and_images.text.text|tag("ocr_text") }}

Your task is to carefully compare the OCR text with what you see in the image and identify ONLY ACTUAL ERRORS.

CRITICAL RULES:
- ONLY report a correction if the ocr_text and expected_text are ACTUALLY DIFFERENT
- If the OCR text matches the image, DO NOT report it as an error
- Do not hallucinate issues - only report what you can clearly see is wrong
- If the OCR is correct, leave the corrections list empty

1. **Missing parts**: Text that appears in the image but is COMPLETELY ABSENT from the OCR output

2. **Corrections**: ONLY include if there is a REAL difference between:
   - ocr_text: The exact text as it appears in the OCR (the wrong version)
   - expected_text: The exact text as it should be according to the image (the correct version)
   - These two MUST be different, otherwise do not include this correction

3. **Overall quality**: good (few/no errors), moderate (some errors), poor (many errors)

If the OCR is perfect, return empty lists for missing_parts and corrections.
"""

[pipe.apply_corrections]
type = "PipeLLM"
description = "Apply the identified corrections to produce the final corrected text"
inputs = { "page.page_view" = "Image", page = "Page", ocr_analysis = "OCRAnalysis" }
output = "Text"
model = "$vision"
system_prompt = "You are a document reconstruction expert. Your job is to produce corrected text by applying identified corrections to OCR output."
prompt = """
You are given:

1. The original page view: $page.page_view

2. The OCR-extracted text:
{{ page.text_and_images.text.text|tag("ocr_text") }}

3. The analysis of OCR issues:

Missing parts that need to be added:
@ocr_analysis.missing_parts

Corrections to apply:
@ocr_analysis.corrections

Overall OCR quality: $ocr_analysis.overall_quality

Your task is to produce the final corrected text by:
- Adding all the missing parts in their correct locations
- Applying all the identified corrections
- Preserving the original structure and formatting
- Using the page view to verify your corrections are accurate

Output only the corrected text, nothing else.
"""

