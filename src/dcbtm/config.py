"""Load ``config.yaml`` and the tables in ``data/raw``."""
from __future__ import annotations

import pandas as pd
import yaml

from .paths import Paths


def _numeric_strings(node, where=""):
    """YAML 1.1 reads 30.0e9 as the STRING '30.0e9'. Find every such value."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _numeric_strings(v, f"{where}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _numeric_strings(v, f"{where}[{i}]")
    elif isinstance(node, str):
        try:
            float(node)
        except ValueError:
            return
        yield f"{where.lstrip('.')} = {node!r}"


def load_config(paths: Paths | None = None) -> dict:
    paths = paths or Paths()
    with open(paths.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    bad = list(_numeric_strings(cfg))
    if bad:
        raise ValueError("config.yaml has numbers that YAML read as strings (write 3.0e+10, not 30.0e9): "
                         + "; ".join(bad))
    return cfg


def load_table(name: str, paths: Paths | None = None) -> pd.DataFrame:
    paths = paths or Paths()
    df = pd.read_csv(paths.raw / f"{name}.csv")
    assert len(df) > 0, f"data/raw/{name}.csv parsed to zero rows"
    return df
