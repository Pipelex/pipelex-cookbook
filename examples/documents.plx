

domain = "documents"
description = "The domain of documents that can comprise pages, text, images, etc. in PDF or other formats"

[concept]
TextAndImagesContent = "A content that comprises text and images where the text can include local links to the images"

[pipe]

[pipe.extract_page_text_from_pdf]
type = "PipeExtract"
description = "Extract page text from a PDF document"
inputs = { document = "PDF" }
output = "Page[]"
max_page_images = 0
page_views = false
model = "extract_ocr_from_document"

[pipe.extract_page_contents_from_pdf]
type = "PipeExtract"
description = "Extract page contents (text and images) from a PDF document"
inputs = { document = "PDF" }
output = "Page[]"
page_views = false

[pipe.extract_page_contents_and_views_from_pdf]
type = "PipeExtract"
description = "Extract page contents (text and images) from a PDF document as well as full page views"
inputs = { document = "PDF" }
output = "Page[]"
max_page_images = 5
page_views = true

