domain = "pdf_vlm_extract"
description = "Extract text from image using OCR, then correct with VLM"
main_pipe = "extract_and_correct"

[concept.OCRCorrection]
description = "A single correction to apply to OCR text"

[concept.OCRCorrection.structure]
ocr_text = { type = "text", description = "The text as extracted by OCR" }
expected_text = { type = "text", description = "The text as it should be" }
correction = { type = "text", description = "Description of the correction" }
location = { type = "text", description = "Location in the document" }

[concept.OCRAnalysis]
description = "Analysis of OCR errors and missing parts"

[concept.OCRAnalysis.structure]
missing_parts = { type = "list", item_type = "text", description = "Text missed by OCR" }
corrections = { type = "list", item_type = "concept", item_concept_ref = "pdf_vlm_extract.OCRCorrection", description = "Corrections to apply" }
overall_quality = { type = "text", description = "OCR quality", choices = ["good", "moderate", "poor"] }

[concept.ExtractedText]
description = "Text extracted from an image via OCR"

[concept.ExtractedText.structure]
text = { type = "text", description = "The extracted text content" }

[pipe]
[pipe.extract_and_correct]
type = "PipeSequence"
description = "Extract text from image then correct with VLM"
inputs = { image = "Image" }
output = "Text"
steps = [
    { pipe = "extract_text", result = "extracted" },
    { pipe = "identify_ocr_issues", result = "ocr_analysis" },
    { pipe = "apply_corrections", result = "corrected_text" },
]

[pipe.extract_text]
type = "PipeLLM"
description = "Extract text from image using VLM as OCR"
inputs = { image = "Image" }
output = "ExtractedText"
model = "$vision"
prompt = """
Image: $image

Extract ALL text from this image exactly as it appears.
Preserve the structure, formatting, and layout.
Output only the extracted text.
"""

[pipe.identify_ocr_issues]
type = "PipeLLM"
description = "Identify OCR errors"
inputs = { image = "Image", extracted = "ExtractedText" }
output = "OCRAnalysis"
model = "$vision"
prompt = """
Image: $image

Extracted text:
@extracted.text

Compare the extracted text with the image. Report ONLY ACTUAL ERRORS:
- missing_parts: Text in image but ABSENT from extraction
- corrections: ONLY if extracted text ≠ what's in the image
- overall_quality: good/moderate/poor

If extraction is correct, return empty lists.
"""

[pipe.apply_corrections]
type = "PipeLLM"
description = "Apply corrections"
inputs = { image = "Image", extracted = "ExtractedText", ocr_analysis = "OCRAnalysis" }
output = "Text"
model = "$vision"
prompt = """
Image: $image

Extracted text:
@extracted.text

Missing parts:
@ocr_analysis.missing_parts

Corrections:
@ocr_analysis.corrections

Output the corrected text only.
"""

