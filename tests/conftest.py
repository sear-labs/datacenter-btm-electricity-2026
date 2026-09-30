"""Shared fixtures. Every stage is computed once per session; the Monte Carlo is the slow part."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from dcbtm import demand, dispatch, lcoe, resilience, scale, utilization
from dcbtm.config import load_config, load_table
from dcbtm.paths import Paths

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def paths() -> Paths:
    return Paths(ROOT)


@pytest.fixture(scope="session")
def cfg(paths) -> dict:
    return load_config(paths)


@pytest.fixture(scope="session")
def published(paths) -> pd.DataFrame:
    return pd.read_csv(paths.published / "published_values.csv")


@pytest.fixture(scope="session")
def stages(cfg, paths, published) -> dict:
    """Everything run_all computes, except figures and maps."""
    disp = dispatch.run(cfg)
    summ = dispatch.summary(disp, cfg)
    costs = load_table("technology_costs", paths)
    t12 = lcoe.lcoe_table(costs, cfg)
    pub_lcoe = {r["row"]: float(r["value"]) for r in published.to_dict("records") if r["item"].startswith("T12.lcoe.")}
    return {
        "bands": demand.figure4_bands(cfg),
        "table9": demand.table9(cfg),
        "dispatch": disp,
        "summary": summ,
        "table11": dispatch.installed_table(cfg),
        "costs": costs,
        "lcoe": t12,
        "blended": lcoe.blended(summ, pub_lcoe),
        "table13": utilization.table13(load_table("asset_utilization", paths), cfg),
        "table3": scale.table3(cfg),
        "tokens_per_second": scale.tokens_per_second(cfg["scale"]["tokens_facility_zettaflops"], cfg),
        "max_btm": resilience.max_btm_output(cfg),
    }


def notebook_cells(path: Path) -> list[str]:
    nb = json.loads(path.read_text(encoding="utf-8"))
    return ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
