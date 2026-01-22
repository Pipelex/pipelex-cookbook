# Blog Article Generator (Pipelex Example)
## Introduction

The Blog Article Generator is an AI-powered content creation tool built using Pipelex pipelines.
It allows users to generate high-quality, SEO-optimized blog posts by simply providing:

Topic
- Target audience
- Writing tone
- Article length

This example demonstrates how to design production-ready AI workflows with multi-step reasoning and cost tracking.

## Overview

This project uses Pipelex to orchestrate multiple LLM calls:

- Generate an SEO outline
- Expand outline into a full blog article
- Display results in terminal
- Save output as a Markdown file

It supports:

- Pipelex Gateway
- Any supported LLM provider (OpenAI, Anthropic, Groq, Mistral, local models, etc.)
- Cost tracking
- Interactive CLI input

## Features

- Interactive CLI input
- SEO title & meta description generation
- Structured outline creation
- Full blog generation
- Cost & token usage tracking
- Saves output automatically
- Modular, production-ready architecture

## Technology Stack

- Pipelex – AI workflow orchestration
- Python 3.10+
- OpenAI / Pipelex Gateway
- AsyncIO
- Pydantic
- TOML (.plx) pipelines

## Project Structure
```bash
blog_article_generator/
│
├── __init__.py
├── blog_article_generator.plx   # Pipeline blueprint
├── blog_article_generator_run.py
├── blog_article_struct.py
├── README.md
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
```python
python examples/wip/blog_article_generator/blog_article_generator_run.py
```

## Example Input
```bash
Enter blog topic: Top AI Startups in 2026
Target audience: Developers
Tone: Professional
Length: Long
```

## Output
- Full blog article
- Markdown file saved automatically
- Cost report per model

Example saved file:
```bash
results/examples/blog_article_generator/blog_article_01.md
```

## Usage
You can change topic every time:
```bash
Enter blog topic: AI Agents in Healthcare
```
No code changes required.

## Cost Tracking

Pipelex automatically prints:

- Model name
- Input tokens
- Output tokens
- Total cost

Example:
```bash
Model: gpt-5
Input tokens: 4,000
Output tokens: 6,200
Cost: $0.0034
```

## Customization

You can modify:

- Prompts in .plx file
- Model selection
- Temperature
- Output format
- Save location

## Use Cases

- Content marketing automation
- SEO blog generation
- Newsletter writing
- Developer documentation
- AI content SaaS
- Startup blogging