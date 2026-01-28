# Blog Article Generator (Pipelex Example)
## Introduction

The Blog Article Generator is an AI-powered content creation tool built using Pipelex pipelines.
It allows users to generate high-quality, SEO-optimized blog posts by simply providing:

Topic
- Target audience
- Writing tone
- Article length

This example demonstrates how to build a simple multi-step blog generation workflow using Pipelex pipelines and structured inputs.

## Overview

This project uses Pipelex to orchestrate multiple LLM calls:

- Generate an SEO-friendly outline
- Expand the outline into a full blog article
- Automatically save results (Markdown, JSON, HTML)
- Inputs are provided via a structured JSON file.

It supports:

- Pipelex Gateway
- Any supported LLM provider (OpenAI, Anthropic, Groq, Mistral, local models, etc.)
- Structured JSON inputs
- Automatic output generation via Pipelex

## Features

- Structured input via JSON
- SEO title & meta description generation
- Outline creation
- Full blog article generation
- Automatic output saving (via Pipelex)
- Clean, minimal PLX-based workflow

## Technology Stack

- Pipelex – AI workflow orchestration
- TOML (.plx) pipelines
- Pipelex CLI
- Any supported LLM provider

## Project Structure

```bash
blog_article_generator/
├── blog_article_generator.plx   # Pipeline definition
├── input.json                   # Example input
├── README.md
└── __init__.py
```

## Getting Started
### Prerequisites

Make sure you have:

- Python 3.10+
- Git
- OpenAI API key OR Pipelex Gateway account

## Installation
### Clone the repository
```bash
git clone https://github.com/Pipelex/pipelex-cookbook.git
cd pipelex-cookbook
```
### Create virtual environment
```python
python -m venv .venv
source .venv/bin/activate
```
### Install dependencies
```python
pip install pipelex --pre
```
### Initialize Pipelex
After installing, run:
```bash
pipelex init
```
You will see a screen like this:

- Pipelex Gateway ⭐ (recommended)
- Anthropic
- Azure OpenAI
- Amazon Bedrock
- Groq
- HuggingFace
- Mistral
- Ollama
- OpenAI
etc.

You can choose ANY provider,
Just select the number from the list.

Example:

- Press 1 → Pipelex Gateway
- Press 12 → OpenAI
- Press 8 → Groq

Pipelex will automatically configure:

- Backends
- Telemetry
- Config files

## Set API Key
### Option A: Pipelex Gateway

Create .env file:
```bash
PIPELEX_GATEWAY_API_KEY=your_key_here
```
Sign up:
👉 https://app.pipelex.com

### Option B: Direct Provider (Example: OpenAI)
```bash
export OPENAI_API_KEY=your_key_here
```
You can use any provider you selected during pipelex init.

**Note**: We use OpenAI API Here.

## Run the Example
```bash
pipelex run examples/wip/blog_article_generator/blog_article_generator.plx \
  -i examples/wip/blog_article_generator/input.json
```

## Example Input
This example uses a structured JSON input file.

```json
{
  "user_prompt": {
    "concept": "BlogArticleRequest",
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

## Output

- SEO-optimized blog outline
- Full blog article in Markdown
- Structured outputs generated automatically by Pipelex

Example output directory:
```bash
results/generate_blog_article_output_01/
```
This directory contains:

- Markdown (.md)
- JSON
- HTML
- Execution graphs
- Working memory artifacts

## Usage

To generate a new article, update the input file:
```bash
"topic": "AI Agents in Healthcare"
```
Then re-run the pipeline.
No changes to the pipeline code are required.

## Customization

You can customize this example by modifying:

- Prompts in the .plx file
- Model selection
- Output format
- Pipeline structure
- Input schema

## Use Cases

- Content marketing automation
- SEO blog generation
- Newsletter drafting
- Developer documentation
- AI-powered content workflows
- Educational content creation