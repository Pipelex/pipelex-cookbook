<div align="center">
  <a href="https://www.pipelex.com/"><img src="https://raw.githubusercontent.com/Pipelex/pipelex/main/.github/assets/logo.png" alt="Pipelex Logo" width="400" style="max-width: 100%; height: auto;"></a>
  <br/>
  <br/>

  <br/>
  <br/>
  <h2 align="center">Pipelex Cookbook 📚</h2>
  <p align="center">Examples, recipes, and best-practice pipelines for the <strong><a href="https://pipelex.com/">Pipelex</a></strong> AI method framework.<br/>
Learn by doing with production-ready examples.</p>

  <div>
    <a href="https://go.pipelex.com/demo"><strong>Demo</strong></a> -
    <a href="https://docs.pipelex.com/"><strong>Documentation</strong></a> -
    <a href="https://docs.pipelex.com/pages/cookbook-examples/"><strong>Cookbook Examples</strong></a> -
    <a href="https://github.com/Pipelex/pipelex-cookbook/issues"><strong>Report Bug</strong></a> -
    <a href="https://github.com/Pipelex/pipelex-cookbook/discussions"><strong>Feature Request</strong></a>
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

<!-- BEGIN methods, written by `make render` from methods/ and cookbook.toml: never edit this region by hand -->

# ⚡ Methods you can run by address

Each of these methods runs on the hosted Pipelex API by its address, from a chatbot, your code or an app, with nothing to install. Its page shows every way to use it, with a sample to try it on.

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

More methods, ready to run the same way, are in the [Pipelex method library](https://github.com/Pipelex/methods).

<!-- END methods -->

**[Recipes](recipes/)** take one way of using a method further, on a real case: a run in your coding agent followed later by its id, the three HTTP calls any tool can make, a FastAPI endpoint, a method over every row of a CSV, a method as a CrewAI agent's tool, a weekly digest.

## 💡 What is Pipelex?

Pipelex is an open-source language that enables you to build and run **repeatable AI methods**. Instead of cramming everything into one complex prompt, you break tasks into focused steps, each pipe handling one clear transformation.

Each pipe processes information using **Concepts** (typing with meaning) to ensure your pipelines make sense. The Pipelex language (`.mthds` files) is simple and human-readable, even for non-technical users. Each step can be structured and validated, giving you the reliability of software with the intelligence of AI.

## 🔧 IDE Extension

We **highly** recommend installing our extension for `.mthds` files into your IDE. You can find it in the [Open VSX Registry](https://open-vsx.org/extension/Pipelex/pipelex). It's coming soon to VS Code marketplace too. If you're using Cursor, Windsurf or another VS Code fork, you can search for it directly in your extensions tab.

## 🤝 Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) to add a method or a recipe.

## 👥 Join the Community

Join our vibrant Discord community to connect with other developers, share your experiences, and get help with your Pipelex projects!

[![Discord](https://img.shields.io/badge/Discord-5865F2?logo=discord&logoColor=white)](https://go.pipelex.com/discord)

## 💬 Support

| Channel | Use case |
| ------- | -------- |
| **GitHub Discussions → "Show & Tell"** | Share ideas, brainstorm, get early feedback. |
| **GitHub Issues** | Report bugs or request features. |
| **Discord** | Real-time chat — [https://go.pipelex.com/discord](https://go.pipelex.com/discord) |
| **Email (privacy & security)** | [security@pipelex.com](mailto:security@pipelex.com) |
| [**Documentation**](https://docs.pipelex.com/) | Comprehensive guides and API reference |

## ⭐ Star Us!

If you find Pipelex helpful, please consider giving us a star on both repositories! It helps us reach more developers and continue improving the tool.

- ⭐ [Main Pipelex Repository](https://github.com/Pipelex/pipelex)
- ⭐ [Pipelex Cookbook Repository](https://github.com/Pipelex/pipelex-cookbook)

## 📝 License

This project is licensed under the [MIT license](LICENSE). Runtime dependencies are distributed under their own licenses via PyPI.

---

*Happy piping!* 🚀

"Pipelex" is a trademark of Evotis S.A.S.

© 2025 Evotis S.A.S.
