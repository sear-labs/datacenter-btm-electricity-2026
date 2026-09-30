"""Committed results equal what the code computes now, and every published number is accounted for.

results/ is committed so a reader sees outputs without running anything (README, "What is
committed"). That is only safe if something fails when the code and the committed results
part ways, which is this file. Tables are written rounded to 6 decimals and compared with a
tolerance, not byte for byte: floating point in NumPy's sin/percentile is not bit-identical
across platforms, and a check that fails on correct behaviour gets switched off.

Figures are not compared here; see test_figures.py.
"""
from __future__ import annotations

import pandas as pd
import pytest

from dcbtm import dispatch, verify

RTOL, ATOL = 1e-9, 1e-6


def _same(committed: pd.DataFrame, fresh: pd.DataFrame, name: str) -> None:
    fresh = fresh.round(6).reset_index(drop=True)
    assert list(committed.columns) == list(fresh.columns), name
    assert len(committed) == len(fresh), name
    for col in committed.columns:
        a, b = committed[col], fresh[col]
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            pd.testing.assert_series_equal(a.astype(float), b.astype(float), check_names=False,
                                           rtol=RTOL, atol=ATOL, obj=f"{name}.{col}")
        else:
            assert a.astype(str).tolist() == b.astype(str).tolist(), f"{name}.{col}"


@pytest.fixture(scope="module")
def check(stages, cfg, published):
    r = {k: stages[k] for k in ("table3", "tokens_per_second", "table9", "table11", "costs", "lcoe",
                                "table13", "blended", "max_btm")}
    return verify.check(r, cfg, published)


FRESH = {
    "table09_demand_monte_carlo.csv": lambda s: s["table9"],
    "fig4_demand_bands.csv": lambda s: s["bands"],
    "fig5_dispatch_24h.csv": lambda s: dispatch.tidy(s["dispatch"]),
    "dispatch_summary.csv": lambda s: s["summary"],
    "table11_installed_capacity.csv": lambda s: s["table11"],
    "table12_lcoe.csv": lambda s: s["lcoe"],
    "table14_blended_lcoe_attempt.csv": lambda s: s["blended"],
    "table13_asset_utilization.csv": lambda s: s["table13"],
    "table03_compute_scale.csv": lambda s: s["table3"],
    "table15_max_btm_output.csv": lambda s: s["max_btm"],
}


@pytest.mark.parametrize("name", sorted(FRESH))
def test_committed_table_matches_the_code(name, paths, stages):
    committed = pd.read_csv(paths.tables / name)
    _same(committed, FRESH[name](stages), name)


def test_every_committed_table_is_checked(paths):
    on_disk = {p.name for p in paths.tables.glob("*.csv")}
    assert on_disk == set(FRESH) | {"reproduction_check.csv"}, on_disk ^ (set(FRESH) | {"reproduction_check.csv"})


def test_committed_reproduction_check_matches_the_code(paths, check):
    committed = pd.read_csv(paths.tables / "reproduction_check.csv")
    _same(committed, check, "reproduction_check.csv")


def test_every_published_claim_has_a_status(check, published):
    claims = published[~published["note"].fillna("").str.contains("operand of")]
    assert len(check) == len(claims) > 100
    assert set(check["status"]) <= {"REPRODUCED", "MATCHES", "CONSISTENT", "DIFFERS", "NO CODE"}


def test_inputs_match_the_paper(check):
    """Every input table (Tables 11, 12 inputs, 13 inputs) is exactly what the paper printed."""
    bad = check[(check["kind"] == "input") & (check["status"] != "MATCHES")]
    assert bad.empty, bad[["item", "published", "computed"]].to_string()


def test_what_does_not_reproduce_is_exactly_the_documented_list(check):
    """The README's list of divergences is this list. A change to either must change both."""
    expected = {
        "S2.2.tokens",
        "T5.total.low.3mile", "T5.total.high.3mile",
        "T12.lcoe.ERCOT Grid (345 kV)", "T12.lcoe.RICE (Natural Gas)", "T12.lcoe.Enhanced Geothermal",
        "T12.lcoe.Small Modular Reactor", "T12.lcoe.Microturbines", "T12.lcoe.Hybrid BESS (LCOS)",
    }
    assert set(check.loc[check["status"] == "DIFFERS", "item"]) == expected
    no_code = set(check.loc[check["status"] == "NO CODE", "item"])
    assert no_code == {f"T14.{k}" for k in ("Baseline", "S1", "S2", "S3", "S4", "S5", "S6")} | {
        f"T15.alolp.S{i}" for i in range(1, 7)}


def test_table9_reproduces_every_cell(check):
    t9 = check[check["table"] == "Table 9"]
    assert len(t9) == 27 and (t9["status"] == "REPRODUCED").all()
    assert t9["basis"].str.contains("truncated").sum() == 26
