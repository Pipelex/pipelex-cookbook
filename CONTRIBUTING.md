# Contributing to **Pipelex Cookbook**

Thank you for sharing your pipeline!  
This repository exists to showcase **working examples**. The most valuable contribution you can make is a **TOML pipeline (or a small set of them) that others can clone, run, and learn from.**

---

## 📑 Quick Checklist

| ✅ Do | 🚫 Don’t |
|-------|---------|
| Put new .toml and .py files under `community/<topic>/<title>/` | Add custom code to `core/` (reserved for curated demos) |
| Add a short comment header describing the pipeline, its inputs, and outputs | Submit a file without context |
| Run `pipelex validate` before committing | Hard-code API keys or secrets |

---

## 1. What Can I Contribute?

* **New pipelines** – end-to-end examples solving a clear task (preferred)  
* **Enhancements** – improved prompts, cheaper model settings, extra comments  
* **Docs** – README snippets, diagrams, walkthroughs

Bug-fixes to existing samples are welcome, but the core Pipelex library lives in the separate `pipelex` repository.

---

## 2. Repository Layout

```

pipelex-cookbook/
├── core/             # Official, curated demos
└── community/        # ⭐ Community contributions
└── <topic>/
├── my\_pipe.toml
└── README.md      (optional extra context)

````

Choose or create a **topic folder** (`rag`, `finance-qa`, `games`, …) that best fits your pipeline.

---

## 3. Before You Start

1. **Fork & clone** this repo.  
2. Run `make install` to set up a virtual environment with Pipelex and test dependencies.  
3. Copy `.env.example` to `.env`, then add at least `OPENAI_API_KEY` (or another key your pipeline needs).  
4. Create a branch:  
   ```bash
   git checkout -b <your-name>/<pipeline>/<slug>
````

---

## 4. Authoring Guidelines

| Aspect             | Rule                                                                                              |
| ------------------ | ------------------------------------------------------------------------------------------------- |
| **File name**      | Use snake\_case, no spaces: `summarize_news.toml`                                                 |
| **Comment header** | `toml<br># Pipeline: Summarize News<br># Inputs: RSS URL<br># Outputs: JSON {title, summary}<br>` |
| **Secrets**        | Read from environment variables; never hard-code keys                                             |
| **Dependencies**   | If needed, list them in `community/<topic>/requirements.txt`                                      |
| **Runability**     | Default config should run on the free or lowest-cost model tier when possible                     |

Someone should be able to run:

```bash
pipelex run community/<topic>/your_pipe.toml
```

and reproduce your results.

---

## 5. Local Sanity Check

```bash
# Validate TOML schema and I/O shapes
make validate-pipes  # wraps `pipelex validate community/**.toml`

# Optional: lint headers, spell-check docs
make lint-docs
```

Passing these checks locally saves time during review.

---

## 6. Opening Your Pull Request

1. Push your branch to your fork.
2. Open a PR to `main` and choose the **Community Pipeline** template.
3. Fill out the checklist (validation passed, description added, external dependencies listed).
4. Keep the PR in **Draft** until CI is green.
5. A maintainer will do a light review; you remain the long-term maintainer of your pipeline.

Use clear titles such as `feat(pipeline): summarise_finance_news` or `add(game_dialogue_gen)`.

---

## 7. Communication Channels

| Purpose                     | Where                                 |
| --------------------------- | ------------------------------------- |
| Ask “is this idea a fit?”   | GitHub **Discussions → Show & Tell**  |
| Report a cookbook bug       | GitHub **Issues**                     |
| Real-time chat / pairing    | **Discord** `#pipeline-contributions` |
| Private or security matters | `security@pipelex.dev`                |

---

## 8. Legal Bits

* **License** – By contributing, you agree your submission is MIT-licensed like the rest of this repo.
* **CLA** – The first time you open a PR, the CLA-assistant bot will guide you through signing the Contributor License Agreement.
* **Code of Conduct** – Be kind. All interactions fall under [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

---

### Thank You!

Pipelines are the heart of Pipelex—every new example helps the community build faster.
Happy piping! 🚀

```
```
