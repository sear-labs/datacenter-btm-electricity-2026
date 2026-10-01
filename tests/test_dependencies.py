"""Every third-party import is declared in pyproject.toml, and the numerical stages need no cartopy.

Reads pyproject.toml rather than restating its list, and scans source rather than
importing it (importing may run the model).
"""
from __future__ import annotations

import ast
import importlib
import re
import sys
import tomllib

import pytest

from conftest import ROOT

# distribution name -> module it installs, where the two differ
MODULE_OF = {"pyyaml": "yaml", "pillow": "PIL"}
SCANNED = ["src", "scripts", "tests"]


def _declared() -> set[str]:
    meta = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    reqs = meta["dependencies"] + [r for extra in meta.get("optional-dependencies", {}).values() for r in extra]
    names = {re.split(r"[<>=!~;\[ ]", r, maxsplit=1)[0].strip().lower() for r in reqs}
    return {MODULE_OF.get(n, n.replace("-", "_")) for n in names}


def _imports() -> dict[str, str]:
    found = {}
    for folder in SCANNED:
        for py in (ROOT / folder).rglob("*.py"):
            for node in ast.walk(ast.parse(py.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    mods = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    mods = [node.module]
                else:
                    continue
                for m in mods:
                    found.setdefault(m.split(".")[0], py.relative_to(ROOT).as_posix())
    return found


def test_scan_finds_imports():
    found = _imports()
    assert {"numpy", "pandas", "matplotlib", "yaml"} <= set(found), "the import scan is not seeing the code"


def test_every_import_is_declared():
    local = {"dcbtm", "conftest"}
    stdlib = set(sys.stdlib_module_names)
    undeclared = {m: f for m, f in _imports().items() if m not in stdlib | local | _declared()}
    assert not undeclared, f"imported but not declared in pyproject.toml: {undeclared}"


class _Refuse:
    """Refuses to import one top-level name, so a transitive import cannot hide."""

    def __init__(self, name):
        self.name = name

    def find_spec(self, fullname, path=None, target=None):
        if fullname == self.name or fullname.startswith(self.name + "."):
            raise ImportError(f"{fullname} is blocked by the test")
        return None


@pytest.mark.parametrize("module", ["dcbtm", "dcbtm.demand", "dcbtm.dispatch", "dcbtm.lcoe", "dcbtm.utilization",
                                    "dcbtm.scale", "dcbtm.resilience", "dcbtm.figures", "dcbtm.verify"])
def test_numerical_stages_import_without_cartopy(module, monkeypatch):
    blocker = _Refuse("cartopy")
    for name in [m for m in sys.modules if m == "cartopy" or m.startswith("cartopy.") or m.startswith("dcbtm")]:
        monkeypatch.delitem(sys.modules, name)
    monkeypatch.setattr(sys, "meta_path", [blocker, *sys.meta_path])
    with pytest.raises(ImportError):
        importlib.import_module("cartopy")  # the blocker itself works
    importlib.import_module(module)
