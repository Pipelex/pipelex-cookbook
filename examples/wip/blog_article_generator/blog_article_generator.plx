domain = "blog_article_generator"
description = "Generate SEO optimized blog articles dynamically"

[concept]
UserPrompt = "User blog request"
ArticleOutline = "SEO optimized outline"
BlogArticle = "Final blog article"

############################################################
# MAIN PIPE
############################################################

[pipe.generate_blog_article]
type = "PipeSequence"
description = "Generate a complete blog article from user prompt"
inputs = { user_prompt = "UserPrompt" }
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
description = "Create SEO friendly blog outline"
model = "gpt-5"
inputs = { user_prompt = "UserPrompt" }
output = "ArticleOutline"
prompt = """
Create SEO outline.

Topic: @user_prompt.topic
Audience: @user_prompt.audience
Tone: @user_prompt.tone
Length: @user_prompt.length

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
description = "Write full blog article using outline"
model = "gpt-5"
inputs = { outline = "ArticleOutline" }
output = "BlogArticle"
prompt = """
Write a full blog article in markdown format using this outline:

@outline

Rules:
- Use headings
- SEO optimized
- Engaging examples
- Professional tone
"""
