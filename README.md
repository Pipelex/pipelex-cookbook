<div align="center">
  <a href="https://www.pipelex.com/"><img src="https://raw.githubusercontent.com/Pipelex/pipelex/main/.github/assets/logo.png" alt="Pipelex Logo" width="400" style="max-width: 100%; height: auto;"></a>
  <br/>
  <br/>

  <br/>
  <br/>
  <h2 align="center">Pipelex Cookbook 📚</h2>
  <p align="center">Worked examples of AI methods, written in MTHDS and run with Pipelex, to read, run and adapt.</p>

  <div>
    <a href="https://go.pipelex.com/docs"><strong>Documentation</strong></a> -
    <a href="https://github.com/Pipelex/pipelex-cookbook/issues"><strong>Report Bug</strong></a> -
    <a href="https://github.com/Pipelex/pipelex-cookbook/discussions"><strong>Discussions</strong></a>
  </div>
  <br/>

  <p align="center">
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT License"></a>
    <br/>
    <a href="https://go.pipelex.com/discord"><img src="https://img.shields.io/badge/Discord-5865F2?logo=discord&logoColor=white" alt="Discord"></a>
    <a href="https://www.youtube.com/@PipelexAI"><img src="https://img.shields.io/badge/YouTube-FF0000?logo=youtube&logoColor=white" alt="YouTube"></a>
    <a href="https://pipelex.com"><img src="https://img.shields.io/badge/Homepage-03bb95?logo=google-chrome&logoColor=white&style=flat" alt="Website"></a>
    <a href="https://github.com/Pipelex/pipelex"><img src="https://img.shields.io/badge/Main_Repo-5a0dad?logo=github&logoColor=white&style=flat" alt="Main Repository"></a>
    <a href="https://docs.pipelex.com/"><img src="https://img.shields.io/badge/Docs-03bb95?logo=read-the-docs&logoColor=white&style=flat" alt="Documentation"></a>
    <br/>
    <br/>
</div>

<!--
Adapted from the onboarding source's front-door and api-key assemblies, last re-read against the rendered files at
Pipelex/.github@75123c4 (onboarding/rendered/front-door.md and onboarding/rendered/api-key.md). Every command, and every
sentence on setting up a door, is a block's own words, so a change lands in the blocks first and is then carried here; where
a sentence of the blocks says "it" for the agent of the sentence before, which this page does not carry, the agent is named.
This page's own are the headings, the sentences sending a reader to a method's page, the two lists `make render` writes between
their BEGIN and END markers, the recipes and tutorial sections, and the closing section on running a method yourself, since
the assembly's last block describes the runtime repository that carries it.
-->

## Try a method in a minute

**Sign up at [app.pipelex.com](https://app.pipelex.com).** Every method below then runs through each of these doors by its address, and its page shows that door's command for it.

### In your chatbot

Add the Pipelex MCP in your chatbot's settings by the address below — in Claude, that is **Add custom connector** — then sign in with your Pipelex account when asked. Nothing to install and no key: the Pipelex MCP runs on your signed-in session.

```
https://mcp.pipelex.com/mcp
```

Give the file as a URL the Pipelex MCP can reach. In ChatGPT you can attach it to the conversation instead and ask for a run on it; Claude has no way yet to hand the Pipelex MCP a file you attached.

Each method's page carries the sentence to paste into your chatbot, with the method's address and its sample.

### In your coding agent

<details open><summary><b>Claude Code</b></summary>

```bash
claude plugin marketplace add Pipelex/pipelex-plugins
claude plugin install pipelex@pipelex-plugins
```

Claude Code asks for an API key when you enable the plugin, and stores it in your OS keychain — create one in your console at [app.pipelex.com](https://app.pipelex.com). The skills, the hook that checks every edit and the Pipelex tools load with it. The plugin's hook and the Pipelex tools run on Node.js, so you need Node.js on your `PATH`.

</details>

<details open><summary><b>Codex</b></summary>

```bash
codex plugin marketplace add Pipelex/pipelex-plugins
export PIPELEX_API_KEY=plx_sk_...     # create one in your console at app.pipelex.com
```

Restart Codex, run `/plugins` to install `pipelex`, and trust the plugin hook on first run. Requires Codex 0.141 or later. The plugin's hook and the Pipelex tools run on Node.js, so you need Node.js on your `PATH`.

</details>

`/pipelex-run` takes the same address as the chatbot, so the sentence on each method's page runs in your coding agent too.

### In your code

Create an API key in your console at [app.pipelex.com](https://app.pipelex.com) and give it to your program as `PIPELEX_API_KEY` — the only thing to configure, since `PIPELEX_BASE_URL` already points at the hosted API.

```bash
export PIPELEX_API_KEY=plx_sk_...
```

Ask your agent to call the method from your TypeScript or Python code, and `/pipelex-integrate` generates the method's types and one typed call that runs it, through the TypeScript SDK [`@pipelex/sdk`](https://www.npmjs.com/package/@pipelex/sdk) or the Python SDK [`pipelex-sdk`](https://pypi.org/project/pipelex-sdk/). Any other software runs a method via API through `POST /v1/start`, with any HTTP client.

Each method's page shows the TypeScript, Python and HTTP calls that run it on its sample.

### As an app

Ask your agent for a webapp around the method, and `/pipelex-scaffold` creates a new app from the [method-app template](https://github.com/Pipelex/pipelex-method-apps) and leaves it running on your machine.

Each method's page carries the one command, `npm create @pipelex/method-app`, that makes the app for that method.

**Next:** [what Pipelex is](https://go.pipelex.com/product) · [documentation](https://go.pipelex.com/docs) · [your console](https://app.pipelex.com) · [Discord](https://go.pipelex.com/discord)

<!-- BEGIN methods, written by `make render` from methods/ and cookbook.toml: never edit this region by hand -->

## Methods you can run by address

Each of these methods runs on the hosted Pipelex API by its address, through every door above, with nothing to install. Its page shows each door's command for it, with a sample to try it on.

- **[Advisory board consultation](methods/advisory_board/)**: Read a business problem told in plain words, consult five to ten expert advisory boards on it, and return one strategic report in Markdown with their consensus, the choices they disagree on, a phased roadmap, risks, resources and success metrics.
- **[Document question answering](methods/answer_from_documents/)**: Read a set of documents and a question, and return a short answer with the verbatim passages it rests on, a confidence level, and a status saying whether the documents answer it fully, in part, or not at all.
- **[Blog article generation](methods/blog_article_generator/)**: Read a topic, an audience, a tone and a length, and return an SEO-optimized blog article in Markdown with its SEO title and meta description.
- **[Discord newsletter](methods/discord_newsletter/)**: Read a week of Discord channel messages and return an HTML newsletter with a weekly summary, the new members, a section per channel and the geographic hubs.
- **[Energy diagnostic (DPE) extraction](methods/extract_dpe/)**: Read a French energy performance diagnostic (DPE) and return the dwelling's address, the issue and expiry dates, the energy and CO₂ classes with their figures per m², and the estimated yearly energy costs.
- **[Gantt chart extraction](methods/extract_gantt/)**: Read a Gantt chart image and return every task with its start and end dates, and every milestone with its date.
- **[Generic document extraction](methods/extract_generic/)**: Read any document and return each page as Markdown, including the text that only appears inside its images and diagrams.
- **[Slide deck extraction](methods/extract_slides/)**: Read a slide deck in PDF and return one Markdown text giving each slide its title, its text and a description of its layout and charts.
- **[Synthetic expense data generation](methods/gen_expense_data/)**: Take a number of employees and return, for each, three or four expense claims with a photographed receipt image and a label saying whether the claim is legitimate or a weekend, inflated, mismatched or vague one, plus an HTML expense report.
- **[Synthetic data generation](methods/gen_synthetic_data/)**: Read a description of a record and a count, and return that many varied synthetic records, here student profiles with their performance, learning style, background, interests and preferences.
- **[Research report](methods/research_report/)**: Read a research question and return a Markdown report with an executive summary, key findings and open questions, drafted from three angles out of the model's own knowledge without searching any source, so it is a first draft to check rather than verified research.

<!-- END methods -->

<!-- BEGIN library, written by `make render` from library.json: never edit this region by hand -->

## Methods from the library

More methods are published in the [Pipelex method library](https://github.com/Pipelex/methods/tree/v0.1.2), and each runs by its address the same way, through every door above. They are listed here as released at v0.1.2.

- **[CV Analyzer](https://github.com/Pipelex/methods/tree/v0.1.2/methods/cv_analyzer)** · `github.com/Pipelex/methods/cv_analyzer@v0.1.2`: End-to-end candidate screening: extract a CV and a job offer, analyze the match, then either generate tailored interview questions or draft a courteous refusal email.
- **[Document Summarizer](https://github.com/Pipelex/methods/tree/v0.1.2/methods/doc_summarizer)** · `github.com/Pipelex/methods/doc_summarizer@v0.1.2`: Deep document summarization: profile the document and extract importance-ranked key points in parallel, then synthesize a structured summary with themes and open questions.
- **[Documents](https://github.com/Pipelex/methods/tree/v0.1.2/methods/documents)** · `github.com/Pipelex/methods/documents@v0.1.2`: Document extraction methods for text, images, and page views.
- **[Image Generation](https://github.com/Pipelex/methods/tree/v0.1.2/methods/image_generation)** · `github.com/Pipelex/methods/image_generation@v0.1.2`: Image generation methods: render a description directly, or refine it into an optimized image prompt first.
- **[Invoice Extraction](https://github.com/Pipelex/methods/tree/v0.1.2/methods/invoice_extraction)** · `github.com/Pipelex/methods/invoice_extraction@v0.1.2`: Extract structured invoice data from a document: classify each page as bill or receipt, then extract amounts, VAT, vendor and buyer details using both the OCR text and the page view.
- **[Slide Designer](https://github.com/Pipelex/methods/tree/v0.1.2/methods/slide_designer)** · `github.com/Pipelex/methods/slide_designer@v0.1.2`: Turn a rough slide-deck brief into design proposals: polish the brief, generate multiple visual themes, render a mockup image for each, and compose an HTML report presenting them all.
- **[Table Extraction](https://github.com/Pipelex/methods/tree/v0.1.2/methods/table_extraction)** · `github.com/Pipelex/methods/table_extraction@v0.1.2`: Extract a data table from a screenshot into faithful HTML, then review the result against the image to correct text and formatting.
- **[Text Stats](https://github.com/Pipelex/methods/tree/v0.1.2/methods/text_stats)** · `github.com/Pipelex/methods/text_stats@v0.1.2`: Deterministic text statistics computed in pure Python: character, word, sentence and paragraph counts, vocabulary richness, most frequent words, and estimated reading and speaking times, reported as Markdown.
- **[Tweet Optimizer](https://github.com/Pipelex/methods/tree/v0.1.2/methods/tweet_optimizer)** · `github.com/Pipelex/methods/tweet_optimizer@v0.1.2`: Optimize a tech tweet: score the draft for fluffiness, cringiness, humblebragging and vagueness, then rewrite it in your own writing style following Twitter/X best practices.

<!-- END library -->

## Recipes

A [recipe](recipes/) takes one way of using a method further, on a real case, calling it by an address pinned to a release tag.

- **[Run a method](recipes/README.md#run-a-method)**: from your coding agent, then followed later by its run id, or with the three HTTP calls any tool can make.
- **[Put a method in your code](recipes/README.md#put-a-method-in-your-code)**: in Python, a FastAPI endpoint, a method over every row of a CSV, a CrewAI agent's tool and a weekly digest; in TypeScript, a Next.js server action, a run read hours after it started, and a local file sent through an upload grant.
- **[Make it an app](recipes/README.md#make-it-an-app)**: from an address to a web app you deploy, and a second method as a second tab of that app.
- **[Make it yours](recipes/README.md#make-it-yours)**: a published method copied, changed and saved to your account, and a new method designed from a sentence and proven by a lab.

## Write a method by hand

Your coding agent writes methods for you, but you can write one yourself: the [tutorial](tutorial/README.md) teaches MTHDS, the language methods are written in, from a first pipe to structured outputs, model settings, batches and parallel steps.

The Pipelex extension highlights `.mthds` files and draws their flowcharts: install it from the [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=pipelex.pipelex), or from the [Open VSX Registry](https://open-vsx.org/extension/Pipelex/pipelex) for Cursor, Windsurf and other VS Code forks.

## Run a method on your own machine

With the Pipelex runtime and your own provider keys ([set it up](https://docs.pipelex.com/latest/get-started/run-it-yourself/)), download the sample inputs a method's page links, then run the method by the address its page names:

```bash
curl -sLo inputs.json <the inputs.json link on the method's page>
pipelex run method <the method's address> --inputs inputs.json
```

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) to add a method or a recipe.

## Join the Community

Join our vibrant Discord community to connect with other developers, share your experiences, and get help with your Pipelex projects!

[![Discord](https://img.shields.io/badge/Discord-5865F2?logo=discord&logoColor=white)](https://go.pipelex.com/discord)

## Support

| Channel | Use case |
| ------- | -------- |
| **GitHub Discussions → "Show & Tell"** | Share ideas, brainstorm, get early feedback. |
| **GitHub Issues** | Report bugs or request features. |
| **Discord** | Real-time chat — [https://go.pipelex.com/discord](https://go.pipelex.com/discord) |
| **Email (privacy & security)** | [security@pipelex.com](mailto:security@pipelex.com) |
| [**Documentation**](https://docs.pipelex.com/) | Comprehensive guides and API reference |

## Star Us!

If you find Pipelex helpful, please consider giving us a star on both repositories! It helps us reach more developers and continue improving the tool.

- ⭐ [Main Pipelex Repository](https://github.com/Pipelex/pipelex)
- ⭐ [Pipelex Cookbook Repository](https://github.com/Pipelex/pipelex-cookbook)

## License

This project is licensed under the [MIT license](LICENSE). Runtime dependencies are distributed under their own licenses via PyPI.

---

*Happy piping!* 🚀

"Pipelex" is a trademark of Evotis S.A.S.

© 2025 Evotis S.A.S.
