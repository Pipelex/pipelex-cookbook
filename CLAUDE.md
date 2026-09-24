# pipelex-cookbook

The cookbook holds Pipelex's example methods as packages runnable by address, each with a generated page. `docs/README.md` explains how it works and `docs/adding-a-method.md` how to add a method. The older examples under `examples/` stay until the new layout replaces them.

- **Method pages are generated.** `methods/<name>/README.md` is written by `make render` from the package (`METHODS.toml`, `inputs.json`, `key.md`, `contract.json`), `cookbook.toml` and `templates/`, and so is the list of methods between the `BEGIN methods` and `END methods` markers of the root `README.md`. Never edit a page or that region by hand: change its sources and run `make render`. `make check-render` fails on any difference.
- **When a bundle changes what its main pipe takes or returns**, run `make refresh` (needs `PIPELEX_API_KEY`) to rewrite its `contract.json`, then `make render`.
- **Keyed checks run by hand.** CI holds no API key, so `make check-hosted` (`check-methods` and `check-addresses`) is run before each pull request that touches a method or a page. No check spends inference; a run on production is started deliberately, once per method.
- **Every manifest carries the cookbook's version** from `pyproject.toml` (`make check-lockstep`).
