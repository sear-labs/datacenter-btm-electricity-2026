"""archive/ is frozen: what produced the published paper, byte for byte.

FROZEN, not append-only: the paper is finished, so any change, addition or removal fails.
A correction goes in src/, and the divergence is recorded; the archive is never edited.
.gitattributes marks archive/** -text so no platform rewrites line endings on checkout.
"""
from __future__ import annotations

import hashlib

from conftest import ROOT

ARCHIVE = ROOT / "archive"
MANIFEST = ARCHIVE / "MANIFEST.sha256"
UNHASHED = {"MANIFEST.sha256", "README.md"}


def _manifest() -> dict[str, str]:
    out = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        digest, rel = line.split(maxsplit=1)
        out[rel] = digest
    return out


def test_manifest_is_not_empty():
    m = _manifest()
    assert len(m) >= 10, f"manifest lists only {len(m)} files"


def test_every_archived_file_is_unchanged():
    for rel, digest in _manifest().items():
        path = ARCHIVE / rel
        assert path.is_file(), f"archived file missing: {rel}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, f"archived file changed: {rel}"


def test_nothing_was_added_to_the_archive():
    on_disk = {p.relative_to(ARCHIVE).as_posix() for p in ARCHIVE.rglob("*") if p.is_file()} - UNHASHED
    assert on_disk == set(_manifest()), f"not in manifest: {sorted(on_disk - set(_manifest()))}"
