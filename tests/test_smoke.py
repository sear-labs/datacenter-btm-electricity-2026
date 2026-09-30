"""Smoke test for the input tables (from sear-labs/code-standard templates/tests, adapted).

Watch it fail:
    pytest -q                                           # green
    <edit data/raw/technology_costs.csv: a negative CapEx>
    pytest -q -k negative                               # MUST go red
    git checkout data/raw/technology_costs.csv
"""
from __future__ import annotations

import pandas as pd
import pytest

from conftest import ROOT

DATA = ROOT / "data" / "raw"
CSVS = sorted(DATA.glob("*.csv"))
SIGNED = {"lat", "lon"}  # coordinates are the only columns allowed below zero


def test_instance_tables_exist():
    assert {p.name for p in CSVS} == {"technology_costs.csv", "asset_utilization.csv", "markets_us.csv",
                                      "markets_global.csv"}


@pytest.mark.parametrize("csv", CSVS, ids=lambda p: p.name)
def test_table_parses_and_is_not_empty(csv):
    df = pd.read_csv(csv)
    assert not df.empty and not df.columns.str.contains("^Unnamed").any(), csv.name


@pytest.mark.parametrize("csv", CSVS, ids=lambda p: p.name)
def test_no_negative_quantities(csv):
    num = pd.read_csv(csv).select_dtypes("number").drop(columns=list(SIGNED), errors="ignore")
    bad = num.lt(0).any()
    assert not bad.any(), f"{csv.name} has negative values in {sorted(bad[bad].index)}"


@pytest.mark.parametrize("csv", CSVS, ids=lambda p: p.name)
def test_no_missing_values(csv):
    assert not pd.read_csv(csv).isna().any().any(), csv.name


def test_capacity_factors_are_fractions():
    cf = pd.read_csv(DATA / "technology_costs.csv")["capacity_factor"]
    assert ((cf > 0) & (cf <= 1)).all()
