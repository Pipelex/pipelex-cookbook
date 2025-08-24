# Web Search Agent Installation Guide

This guide will help you set up the web search agent pipeline in Pipelex.

## Prerequisites

- Python 3.10 or higher
- uv package manager (recommended) or pip
- Serper API key for web search functionality
- LLM API key (OpenAI, Anthropic, or Mistral)

## Step 1: Install Dependencies

### Using uv (Recommended)

```bash
# Install the project with web search dependencies
uv sync

# And install specific web search dependencies
uv add trafilatura python-dateutil limits gradio
```

## Step 2: Environment Configuration

1. Copy the environment example file:
```bash
cp env.example .env
```

2. Edit the `.env` file and add your API keys:
```bash
# Required for web search functionality
SERPER_API_KEY=your_primary_serper_api_key_here
SERPER_API_KEY_FALLBACK=your_fallback_serper_api_key_here

# Required for LLM operations (choose one or more)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
```

## Step 3: Get API Keys

### Serper API Key
1. Go to [Serper.dev](https://serper.dev)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Optionally get a fallback key for redundancy

### LLM API Key
Choose one or more of the following:

- **OpenAI**: Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Anthropic**: Get API key from [Anthropic Console](https://console.anthropic.com/)
- **Mistral**: Get API key from [Mistral AI Platform](https://console.mistral.ai/)

## Step 4: Validate Installation

Run the validation command to ensure everything is set up correctly:

```bash
python -m pipelex.cli._cli validate
```

## Step 5: Test the Web Search Agent

Run the simple test to verify everything works:

```bash
python examples/simple_web_search_test.py
```

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Run `uv sync` or `pip install -r requirements.txt`
2. **API key errors**: Ensure your `.env` file is properly configured
3. **Rate limiting**: The web search module includes rate limiting (360 requests/hour)
4. **Import errors**: Make sure you're in the correct Python environment

### Getting Help

- Check the [main README](README_web_search_agent.md) for detailed usage
- Run `python -m pipelex.cli._cli validate` to check for configuration issues
- Ensure all environment variables are properly set

## Next Steps

Once installation is complete, you can:

1. Run the full demo: `python examples/web_search_agent_example.py`
2. Integrate the web search agent into your own pipelines
3. Customize the search parameters and response generation
4. Add additional LLM providers as needed
