# Recipes

Each method page shows every way to use its method in a few lines. A recipe goes further on one way, on a real case: a small project you copy as one directory, calling its method by an address pinned to a release tag, with code the cookbook's checks hold to that method.

## Put a method in your code

### Python

Each recipe is one script that declares its dependencies inline, so `uv run` installs them and runs it. Every one needs a Pipelex API key in `PIPELEX_API_KEY`, from [app.pipelex.com](https://app.pipelex.com).

| Recipe | What it shows | Method |
|---|---|---|
| [A FastAPI endpoint](code/python/fastapi-endpoint/) | An API answering questions from documents, whose responses are typed by the method's generated models | [Document question answering](../methods/answer_from_documents/) |
| [A method over every row of a CSV](code/python/csv-batch/) | A spreadsheet of invoice links turned into a spreadsheet of totals, a few runs at a time | [Invoice extraction](https://github.com/Pipelex/methods/tree/v0.1.1/methods/invoice_extraction), from the method library |
| [A method as a CrewAI agent's tool](code/python/crewai-tool/) | A crew whose analyst drafts a research brief through the method and whose editor turns it into a memo | [Research report](../methods/research_report/) |
| [A weekly digest](code/python/weekly-digest/) | A week of Discord messages fetched in code, written up by the method, and posted as HTML | [Discord newsletter](../methods/discord_newsletter/) |

To add one, read [docs/adding-a-recipe.md](../docs/adding-a-recipe.md).
