# Pipelex Cookbook 📚

> Examples, recipes, and best-practice pipelines for the **[Pipelex](https://github.com/Pipelex/pipelex)** LLM Pipeline framework.


If you just want to **run** an example, jump to **Quick Start**. If you'd like to **share** your own pipeline, head straight to **Contributing**. :books: Check out the [Pipelex Documentation](https://github.com/Pipelex/pipelex/blob/dev/doc/Documentation.md) for more information.

---

## Table of Contents

1. [Repository Layout](#repository-layout)  
2. [Quick Start](#quick-start)  
3. [Contributing](#contributing)  
4. [Contact & Support](#contact--support)  

---

## Repository Layout

```
.
├── pipelex_libraries/         # Main library code
│   ├── pipelines/             # Pipeline implementations
│   │   ├── base_library/      # Core pipeline components
│   │   ├── community/         # 💡 Community-contributed pipelines
│   │   ├── examples/          # Example pipelines
│   │   └── quick_start/       # Quick start tutorials
│   ├── llm_deck/              # LLM deck components
│   ├── llm_integrations/      # LLM provider integrations
│   └── templates/             # Prompt templates
├── core/                      # Curated, battle-tested demos
│   ├── examples/              # Advanced examples (PDF extraction, expense processing, etc.)
│   └── quick_start/           # Getting started tutorials
└── community/                 # 💡 Your contributions live here!  See Contributing ↓
```

---

## Quick Start

```bash
git clone https://github.com/Pipelex/pipelex-cookbook.git
cd pipelex-cookbook
```

### Prepare your virtual environment

Example using venv:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

### Install Pipelex and other tools for the cookbook

```bash
make install
```

This will install the Pipelex python library and its dependencies using poetry.

### Set up environment variables

```bash
cp .env.example .env
```

Enter your API keys into your `.env` file. The `OPENAI_API_KEY` is enough to get you started, but some pipelines require models from other providers.

### Run Hello World

```bash
python core/quick_start/hello_world.py
```

---

## Contributing

We ❤️ contributions!  Before opening a pull request, please:

1. **Read [`CONTRIBUTING.md`](CONTRIBUTING.md)**.
2. Add your file under **`community/<your-folder>`**; feel free to group related examples by topic.
3. Include a short **README snippet at the top of your TOML** describing purpose, inputs, and expected outputs.
4. Verify the pipeline runs locally with a free/open LLM preset when possible, to lower the entry barrier for reviewers.

> **Tip:** If you're unsure whether your idea fits, open a GitHub **Discussion** first—feedback is fast and public.([GitHub Docs][4])

---

## Contact & Support

| Channel                                | Use case                                                                  |
| -------------------------------------- | ------------------------------------------------------------------------- |
| **GitHub Discussions → "Show & Tell"** | Share ideas, brainstorm, get early feedback.                              |
| **GitHub Issues**                      | Report bugs or request features.                                          |
| **Email (privacy & security)**         | [security@pipelex.com](mailto:security@pipelex.com)                       |
| **Discord**                            | Real-time chat — [https://discord.gg/SReshKQjWt](https://discord.gg/SReshKQjWt) |

---

*Happy piping!* 🚀
