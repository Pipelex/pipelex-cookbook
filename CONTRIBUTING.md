# Contributing to **Pipelex Cookbook**

Thank you for sharing your pipeline!  
This repository exists to showcase **working examples**. The most valuable contribution you can make is a **TOML pipeline (or a small set of them) that others can clone, run, and learn from.**

---

## 📑 Quick Checklist

| ✅ Do | 🚫 Don’t |
|-------|---------|
| Put new code files under `wip/` paths | Add custom code to `examples/` (reserved for curated demos) |
| Run `pipelex validate` before committing | Hard-code API keys or secrets |

---

## What Can I Contribute?

* **New pipelines** – end-to-end examples solving a clear task (preferred)  
* **Enhancements** – improved prompts, cheaper model settings, extra comments  
* **Docs** – README snippets, diagrams, walkthroughs

Bug-fixes to existing samples are welcome, but the core Pipelex library lives in the separate [Pipelex](https://github.com/Pipelex/pipelex) repository.

---

## Repository Layout

```

pipelex-cookbook/
├── examples/             # Official, curated demos
└── wip/                  # Work in progress
└── quick_start/                  # Quick start examples
└── pipelex_libraries/pipelines/<topic>/your_pipe.toml

```

Choose or create a **topic folder** (`finance`, `games`, …) that best fits your pipeline.

---

## Before You Start

1. **Fork & clone** this repo.  
2. Run `make install` to set up a virtual environment with Pipelex and test dependencies.  
3. Copy `.env.example` to `.env`, then add at least `OPENAI_API_KEY` (or another key your pipeline needs).  
4. Create a branch:  
```bash
   git checkout -b <your-name>/<pipeline>/<slug>
```

---

## Local Sanity Check

```bash
# Validate TOML schema and I/O shapes
make validate  # wraps `pipelex validate`
```

---

## Opening Your Pull Request

1. Push your branch to your fork.
2. Open a PR to `main` and choose the **Community Pipeline** template.
3. Fill out the checklist (validation passed, description added, external dependencies listed).
4. Keep the PR in **Draft** until CI is green.
5. A maintainer will do a light review; you remain the long-term maintainer of your pipeline.

---

## Communication Channels

| Purpose                     | Where                                 |
| --------------------------- | ------------------------------------- |
| Ask “is this idea a fit?”   | GitHub **Discussions → Show & Tell**  |
| Report a cookbook bug       | GitHub **Issues**                     |
| Real-time chat / pairing    | **Discord** `#pipeline-contributions` |
| Private or security matters | `security@pipelex.com`                |

---

## Legal Bits & Rules

* **CLA** – The first time you open a PR, the CLA-assistant bot will guide you through signing the Contributor License Agreement. The process signature uses the [CLA assistant lite](https://github.com/marketplace/actions/cla-assistant-lite).
* **Code of Conduct** – Be kind. All interactions fall under [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

---

## Thank You!

Pipelines are the heart of Pipelex: every new example helps the community build faster.
Happy piping! 🚀
