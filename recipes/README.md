# Recipes

Each method page shows every way to use its method in a few lines. A recipe goes further on one way, on a real case, calling its method by an address pinned to a release tag: a request to your coding agent, a few HTTP calls, or a small project you copy as one directory, with code the cookbook's checks hold to that method.

## Run a method

These recipes run a method with nothing to build: from your coding agent, or with any tool that makes HTTP calls. Each run spends credit on your Pipelex account.

| Recipe | What it shows | Method |
|---|---|---|
| [A run in your coding agent, followed later by its id](run/coding-agent/) | `/pipelex-run` in Claude Code or Codex starting a run by its address, then following it from another session by its id alone and saving it to `runs/<run_id>/` | [Research report](../methods/research_report/) |
| [A method over HTTP: start, poll, results](run/http/) | The three calls that run a method from a shell script with `curl`, each outcome with its own exit status, and how n8n, Zapier or any tool that makes HTTP calls makes the same calls | [Energy diagnostic (DPE) extraction](../methods/extract_dpe/) |

## Put a method in your code

### Python

Each recipe is one script that declares its dependencies inline, so `uv run` installs them and runs it. Every one needs a Pipelex API key in `PIPELEX_API_KEY`, from [app.pipelex.com](https://app.pipelex.com).

| Recipe | What it shows | Method |
|---|---|---|
| [A FastAPI endpoint](code/python/fastapi-endpoint/) | An API answering questions from documents, whose responses are typed by the method's generated models | [Document question answering](../methods/answer_from_documents/) |
| [A method over every row of a CSV](code/python/csv-batch/) | A spreadsheet of invoice links turned into a spreadsheet of totals, a few runs at a time | [Invoice extraction](https://github.com/Pipelex/methods/tree/v0.1.1/methods/invoice_extraction), from the method library |
| [A method as a CrewAI agent's tool](code/python/crewai-tool/) | A crew whose analyst drafts a research brief through the method and whose editor turns it into a memo | [Research report](../methods/research_report/) |
| [A weekly digest](code/python/weekly-digest/) | A week of Discord messages fetched in code, written up by the method, and posted as HTML | [Discord newsletter](../methods/discord_newsletter/) |

### TypeScript

Each recipe is a small package calling the method through [`@pipelex/sdk`](https://www.npmjs.com/package/@pipelex/sdk): `npm install` sets it up, on Node.js 22.12 or later. Every one needs a Pipelex API key in `PIPELEX_API_KEY`, from [app.pipelex.com](https://app.pipelex.com).

| Recipe | What it shows | Method |
|---|---|---|
| [A Next.js form whose server action runs a method](code/typescript/nextjs-server-action/) | A page whose form is validated against the method's input type and whose server action renders its typed output, with the key kept on the server | [Blog article generator](../methods/blog_article_generator/) |
| [A run started now and read hours later](code/typescript/durable-run/) | One command that starts a run and exits with its id, and another that reads the result by that id whenever it is ready | [Research report](../methods/research_report/) |
| [A local file sent through an upload grant](code/typescript/upload-grant/) | An image from this machine sent to storage with a one-time grant, then read by the method by its storage uri | [Gantt chart extraction](../methods/extract_gantt/) |

To add one, read [docs/adding-a-recipe.md](../docs/adding-a-recipe.md).
