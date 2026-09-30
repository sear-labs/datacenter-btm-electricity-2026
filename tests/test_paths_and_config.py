"""Root resolution honours or refuses a NAMED location, and config numbers are numbers."""
from __future__ import annotations

import pytest
import yaml

from conftest import ROOT
from dcbtm.config import _numeric_strings
from dcbtm.paths import Paths, RootNotFound


def test_explicit_root_is_used(tmp_path):
    assert Paths(ROOT).root == ROOT


def test_a_named_root_that_is_wrong_is_refused_not_replaced(tmp_path, monkeypatch):
    """Falling through to the next candidate would silently hand back the published inputs."""
    monkeypatch.chdir(ROOT)  # a valid fallback IS available; it must not be used
    with pytest.raises(RootNotFound):
        Paths(tmp_path)
    monkeypatch.setenv("DCBTM_ROOT", str(tmp_path))
    with pytest.raises(RootNotFound):
        Paths()


def test_env_root_is_used(monkeypatch):
    monkeypatch.setenv("DCBTM_ROOT", str(ROOT))
    assert Paths().root == ROOT


def test_yaml_scientific_notation_trap_is_caught():
    bad = yaml.safe_load("a: 30.0e9\nb: 3.0e+10\n")
    assert list(_numeric_strings(bad)) == ["a = '30.0e9'"]


def test_config_has_no_numbers_read_as_strings(cfg):
    assert not list(_numeric_strings(cfg))
