"""No credential-shaped value in any text file the repository ships.

This prevents the SECOND exposure (a key pasted back from an old notebook); it cannot undo a
first, which needs the credential rotated. The canary test proves the patterns can fire.
"""
from __future__ import annotations

import re

import pytest

from conftest import ROOT

PATTERNS = {
    "github token": r"gh[pousr]_[A-Za-z0-9]{36,}",
    "aws key": r"AKIA[0-9A-Z]{16}",
    "openai/anthropic key": r"(?<![A-Za-z0-9])sk-(?:ant-)?[A-Za-z0-9_-]{20,}",  # not the tail of "risk-..."
    "google api key": r"AIza[0-9A-Za-z_-]{35}",
    "private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "gurobi wls": r"WLS(?:ACCESSID|SECRET)\W{1,5}[0-9a-f-]{20,}",
    "assigned secret": r"(?i)(?:api[_-]?key|secret|password|passwd|token)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]",
    "bearer": r"(?i)authorization:\s*bearer\s+[A-Za-z0-9._-]{20,}",
}
TEXT = {".py", ".md", ".txt", ".csv", ".yaml", ".yml", ".toml", ".cff", ".bib", ".ipynb", ".json", ".cfg", ""}
SKIP_DIRS = {".git", ".pytest_cache", ".ruff_cache", "__pycache__", ".claude"}


def _files():
    for p in ROOT.rglob("*"):
        if p.is_file() and not SKIP_DIRS & set(p.relative_to(ROOT).parts) and p.suffix.lower() in TEXT \
                and not p.name.endswith(".egg-info"):
            yield p


def _hits(text: str) -> list[str]:
    return [name for name, pat in PATTERNS.items() if re.search(pat, text)]


@pytest.mark.parametrize("sample,kind", [
    ("token = 'ghp_" + "a" * 36 + "'", "github token"),
    ("WLSSECRET: " + "0123abcd-" * 3, "gurobi wls"),
    ('API_KEY="' + "x" * 16 + '"', "assigned secret"),
])
def test_patterns_fire_on_a_canary(sample, kind):
    assert kind in _hits(sample)


def test_a_url_slug_is_not_a_key():
    """A cited URL, '...new-risk-to-u-s-power-grid-stability', matched the key pattern once."""
    assert not _hits("https://example.org/emerging-as-new-risk-to-u-s-power-grid-stability/")
    assert "openai/anthropic key" in _hits("key: sk-" + "A1b2" * 6)


def test_scan_sees_the_repository():
    names = {p.name for p in _files()}
    assert {"README.md", "config.yaml", "scenarios_gen.ipynb", "run_all.py"} <= names


def test_no_credential_shaped_values():
    found = {p.relative_to(ROOT).as_posix(): h for p in _files() if (h := _hits(p.read_text("utf-8", "replace")))}
    assert not found, found
