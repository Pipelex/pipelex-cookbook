"""The tutorial's bundles, which `make check-methods` validates on production from their files.

Each lesson under `tutorial/` is a single self-contained `.mthds` file, with its own domain and main pipe and no manifest, so the check validates
each one alone, with its path from the repository root as its source, and needs no package and no contract. No page is rendered from the
tutorial, so `make refresh` does not touch it.
"""

from pathlib import Path

TUTORIAL_DIR = "tutorial"


def tutorial_bundles(root: Path) -> list[Path]:
    """Every `.mthds` file under `tutorial/`, at any depth, sorted by path."""
    tutorial_dir = root / TUTORIAL_DIR
    if not tutorial_dir.is_dir():
        return []
    return sorted(path for path in tutorial_dir.rglob("*.mthds") if path.is_file())
