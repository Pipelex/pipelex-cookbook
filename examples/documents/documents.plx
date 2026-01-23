

domain = "documents"
description = "The domain of documents that can comprise pages, text, images, etc. in other formats"

[pipe]
[pipe.extract_page_contents_and_views_from_pdf]
type = "PipeExtract"
description = "Extract page contents (text and images) from a document as well as full page views"
inputs = { document = "Document" }
output = "Page[]"
max_page_images = 5
page_views = true

