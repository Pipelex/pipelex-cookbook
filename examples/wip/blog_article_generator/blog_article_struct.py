from pipelex.core.stuffs.structured_content import StructuredContent
from pydantic import Field

class UserPrompt(StructuredContent):
    topic: str = Field(..., description="Blog topic")
    audience: str = Field(..., description="Target audience")
    tone: str = Field(..., description="Writing tone")
    length: str = Field(..., description="Short / Medium / Long")

class ArticleOutline(StructuredContent):
    seo_title: str
    meta_description: str
    headings: list[str]

class BlogArticle(StructuredContent):
    content: str
