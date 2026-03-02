# Blog Article Generator

Generate SEO-optimized blog articles from a structured request (topic, audience, tone, length).

## Prerequisites

Before running this example, ensure you have set up your environment. See the [Clone and Install](../../../README.md#1-clone-and-install) section in the main README.

## Run the pipeline

```bash
pipelex run bundle examples/wip/blog_article_generator/bundle.mthds -i examples/wip/blog_article_generator/inputs.json
```

## Example input

```json
{
  "user_prompt": {
    "concept": "blog_article_generator.BlogArticleRequest",
    "content": {
      "text": "Write a fun and engaging blog article",
      "topic": "Capybara",
      "audience": "Kids",
      "tone": "Casual",
      "length": "Short"
    }
  }
}
```

## Flowchart

![Flowchart](flowchart.png)

## Expected output

![Expected output](expected_output.png)

## How it works

This pipeline uses a `PipeSequence` with two steps to go from a structured request to a finished article:

1. **`create_outline`** (`PipeLLM`) -- Takes the `BlogArticleRequest` input and generates an `ArticleOutline` containing an SEO title, meta description, and headings.
2. **`write_article`** (`PipeLLM`) -- Takes the generated `ArticleOutline` and writes the full `BlogArticle` in markdown format, matching the requested tone.

### Concepts

| Concept | Role |
|---|---|
| `BlogArticleRequest` | Structured input with fields: `text`, `topic`, `audience`, `tone`, `length` |
| `ArticleOutline` | Intermediate outline (SEO title, meta description, headings) |
| `BlogArticle` | Final blog article in markdown |

## Go further

You can generate the Python structures and runner code from this bundle:

```bash
pipelex build runner bundle examples/wip/blog_article_generator/bundle.mthds
```
