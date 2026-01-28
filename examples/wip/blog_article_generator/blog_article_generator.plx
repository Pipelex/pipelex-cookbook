domain = "blog_article_generator"
description = "Generate SEO optimized blog articles dynamically"
main_pipe = "generate_blog_article"

############################################################
# CONCEPTS
############################################################

[concept]
BlogArticleRequest = "Structured request describing the blog article to generate (topic, audience, tone, length)"
ArticleOutline = "SEO optimized blog outline"
BlogArticle = "Final blog article"

############################################################
# MAIN PIPE
############################################################

[pipe.generate_blog_article]
type = "PipeSequence"
description = "Generate a complete blog article from a blog article request"
inputs = { user_prompt = "BlogArticleRequest" }
output = "BlogArticle"
steps = [
    { pipe = "create_outline", result = "outline" },
    { pipe = "write_article", result = "article" },
]

############################################################
# STEP 1 - CREATE OUTLINE
############################################################

[pipe.create_outline]
type = "PipeLLM"
description = "Create an SEO-friendly blog outline from the blog article request"
model = "gpt-5"
inputs = { user_prompt = "BlogArticleRequest" }
output = "ArticleOutline"
prompt = """
Create an SEO-friendly blog outline based on the following request:

@user_prompt

Return:
- seo_title
- meta_description
- headings
"""

############################################################
# STEP 2 - WRITE ARTICLE
############################################################

[pipe.write_article]
type = "PipeLLM"
description = "Write the full blog article in markdown using the generated outline"
model = "gpt-5"
inputs = { outline = "ArticleOutline" }
output = "BlogArticle"
prompt = """
Write a full blog article in markdown format using the following outline:

@outline

Rules:
- Use clear markdown headings
- SEO optimized
- Include engaging examples
- Match the requested tone
"""
