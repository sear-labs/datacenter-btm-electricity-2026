"""Where the repository's inputs and outputs live.

The inputs (``config.yaml``, ``data/``, ``archive/``) are not package data: a
``pip install git+https://...`` ships ``src/dcbtm`` and nothing else. So the root is
resolved in this order, and a NAMED location is honoured or refused, never silently
replaced by the next candidate:

    1. an explicit ``root`` argument      named: must hold config.yaml, or this raises
    2. the ``DCBTM_ROOT`` environment var  named: same rule
    3. the checkout this package sits in   a clone or an editable install
    4. the current working directory       a script run from the repo root

There is no download fallback. This is a paper repository: clone it.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "config.yaml"


class RootNotFound(FileNotFoundError):
    pass


def _is_root(p: Path) -> bool:
    return (p / MARKER).is_file() and (p / "data" / "raw").is_dir()


def resolve_root(root: str | os.PathLike | None = None) -> Path:
    if root is not None:
        p = Path(root).resolve()
        if not _is_root(p):
            raise RootNotFound(f"root={p} was given explicitly but holds no {MARKER} and data/raw/")
        return p
    env = os.environ.get("DCBTM_ROOT")
    if env:
        p = Path(env).resolve()
        if not _is_root(p):
            raise RootNotFound(f"DCBTM_ROOT={p} is set but holds no {MARKER} and data/raw/")
        return p
    here = Path(__file__).resolve()
    if len(here.parents) > 2 and _is_root(here.parents[2]):  # <root>/src/dcbtm/paths.py
        return here.parents[2]
    cwd = Path.cwd().resolve()
    if _is_root(cwd):
        return cwd
    raise RootNotFound(
        "Could not find the repository root (a folder holding config.yaml and data/raw/). "
        "The inputs are not installed with the package: clone the repository and either "
        "run from its root, install it with `pip install -e .`, or set DCBTM_ROOT."
    )


class Paths:
    def __init__(self, root: str | os.PathLike | None = None):
        self.root = resolve_root(root)
        self.config = self.root / MARKER
        self.raw = self.root / "data" / "raw"
        self.published = self.root / "data" / "published"
        self.archive = self.root / "archive"
        self.results = self.root / "results"
        self.tables = self.results / "tables"
        self.figures = self.results / "figures"

    def ensure_outputs(self) -> None:
        self.tables.mkdir(parents=True, exist_ok=True)
        self.figures.mkdir(parents=True, exist_ok=True)
