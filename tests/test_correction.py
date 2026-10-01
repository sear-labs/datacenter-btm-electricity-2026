"""The authors' correction (README, "Correction to the published article").

Two kinds of check. The README's corrected numbers, rankings and published-value columns must
agree with what the code computes and with data/published/, so the prose cannot drift from the
run. And the year-long dispatch behind them must obey its own physics.

Watch it fail:
    pytest -q tests/test_correction.py                  # green
    <edit README.md: S4's corrected blended LCOE 59.55 -> 59.65>
    pytest -q tests/test_correction.py -k readme        # MUST go red
    git checkout README.md
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
import pytest

from conftest import ROOT
from dcbtm import correction

PUBLISHED_COL = re.compile(r"published", re.I)


def _section() -> str:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    start = text.index("## Correction to the published article")
    end = text.index("\n## ", start + 5)
    return text[start:end]


def _tables(section: str) -> list[pd.DataFrame]:
    """Every pipe table in the section whose header has a 'published' and a 'corrected' column."""
    out, block = [], []
    for line in section.splitlines() + [""]:
        if line.startswith("|"):
            block.append([c.strip() for c in line.strip("|").split("|")])
            continue
        if len(block) > 2 and any(PUBLISHED_COL.search(h) for h in block[0]):
            out.append(pd.DataFrame(block[2:], columns=block[0]))
        block = []
    return [t for t in out if len(t.columns) == 3]


def _num(cell: str) -> float:
    return float(cell.lstrip(">"))


@pytest.fixture(scope="module")
def readme_tables():
    t = _tables(_section())
    assert len(t) == 3, f"expected the Table 12, 14 and 15 correction tables, found {len(t)}"
    return dict(zip(("table12", "table14", "table15"), t))


@pytest.fixture(scope="module")
def corr(stages):
    return stages["correction"]


def _mixed(df: pd.DataFrame, col: str) -> pd.Series:
    return df[df["year"] == "mixed"].set_index("scenario")[col]


def _published(published: pd.DataFrame, prefix: str) -> dict[str, float]:
    p = published[published["item"].str.startswith(prefix)]
    return dict(zip(p["row"], p["value"].astype(float)))


def test_readme_table12_matches_the_code_and_the_paper(readme_tables, stages, published):
    t = readme_tables["table12"]
    lc = stages["lcoe"].set_index("technology")["lcoe_usd_per_mwh"]
    pub = _published(published, "T12.lcoe.")
    assert list(t.iloc[:, 0]) == list(lc.index)
    for row in t.itertuples(index=False):
        assert _num(row[1]) == pub[row[0]], row
        assert _num(row[2]) == round(lc[row[0]], 2), row


def test_readme_table14_matches_the_code_and_the_paper(readme_tables, corr, published):
    t = readme_tables["table14"]
    blend = _mixed(corr["table14"], "blended_lcoe_usd_per_mwh")
    pub = _published(published, "T14.")
    assert len(t) == len(blend)
    for row in t.itertuples(index=False):
        key = row[0].split()[0]
        assert _num(row[1]) == pub[row[0]], row
        assert _num(row[2]) == round(blend[key], 2), row


def test_readme_table15_matches_the_code_and_the_paper(readme_tables, corr, published):
    t = readme_tables["table15"]
    alolp = _mixed(corr["table15"], "alolp_pct")
    pub = _published(published, "T15.alolp.")
    assert len(t) == len(alolp)
    for row in t.itertuples(index=False):
        key = row[0].split(":")[0]
        assert _num(row[1]) == pub[row[0]], row
        x = alolp[key]
        if row[2].startswith(">"):  # shown as ">99.9" when it rounds to 100.0 but is not 100
            assert _num(row[2]) < x < 100, row
        else:
            assert _num(row[2]) == round(x, 1), row


def _ranking(section: str, phrase: str) -> list[str]:
    m = re.search(phrase + r" (?:was|is) ([^;.]+)", section)
    assert m, phrase
    return [s.strip() for s in m.group(1).split(",")]


def test_readme_rankings_follow_the_numbers(corr, published):
    sec = _section()
    blend = _mixed(corr["table14"], "blended_lcoe_usd_per_mwh")
    assert _ranking(sec, "As corrected, the ranking from cheapest") == list(blend.sort_values().index)
    pub14 = {k.split()[0]: v for k, v in _published(published, "T14.").items()}
    assert _ranking(sec, "As published, the ranking from cheapest") == sorted(pub14, key=pub14.get)
    alolp = _mixed(corr["table15"], "alolp_pct")
    assert _ranking(sec, "As corrected, the ranking from highest ALOLP") == list(
        alolp.sort_values(ascending=False).index)
    pub15 = {k.split(":")[0]: v for k, v in _published(published, "T15.alolp.").items()}
    assert _ranking(sec, "As published, the ranking from highest ALOLP") == sorted(pub15, key=lambda k: -pub15[k])


def test_readme_spike_year_sentence_matches_the_code(corr):
    sec = _section()
    m = re.search(r"Spike\)\s+days, the same calculation gives (.+?)\.\s", sec)
    assert m
    said = dict(re.findall(r"(S\d) (\d+\.\d)", m.group(1)))
    spike = corr["table15"][corr["table15"]["year"] == "spike"].set_index("scenario")["alolp_pct"]
    assert said == {k: f"{v:.1f}" for k, v in spike.items()}
    assert list(spike.sort_values(ascending=False).index) == list(
        _mixed(corr["table15"], "alolp_pct").sort_values(ascending=False).index)  # "the order is the same"


def test_readme_unserved_sentence_matches_the_code(corr):
    m = re.search(r"so ([\d,]+) MWh a year \((\d+\.\d) % of the load\) goes unserved", _section())
    assert m
    e = corr["energy"]
    short = e[(e["year"] == "mixed") & (e["unserved_mwh"] > 0)]
    assert list(short["scenario"]) == ["S6"]
    r = short.iloc[0]
    assert m.group(1) == f"{r.unserved_mwh:,.0f}"
    assert m.group(2) == f"{100 * r.unserved_mwh / r.load_mwh:.1f}"


# ---- the year-long dispatch obeys its own rules -------------------------------------------

@pytest.fixture(scope="module")
def years(cfg):
    return {k: correction.hourly_year(k, cfg) for k in ("mixed", "spike")}


def test_year_shape_and_composition(years, cfg):
    for load in years.values():
        assert load.shape == (8760,)
        assert 0 <= load.min() and load.max() <= cfg["dispatch"]["facility_mw"]
    # the mixed year is lighter than a year of spike days, and weekends are lighter than weekdays
    assert years["mixed"].mean() < years["spike"].mean()
    days = years["mixed"].reshape(365, 24).mean(axis=1)
    weekday = np.arange(365) % 7 < cfg["correction"]["weekdays_per_week"]
    assert days[~weekday].max() < days[weekday].mean()


@pytest.mark.parametrize("kind", ["mixed", "spike"])
@pytest.mark.parametrize("key", ["S1", "S2", "S3", "S4", "S5", "S6"])
def test_dispatch_year_physics(key, kind, years, cfg):
    load = years[kind]
    o = correction.dispatch_year(key, load, cfg)
    p = cfg["dispatch"]["scenarios"][key]
    supplied = sum(o[s] for s in correction.SOURCES)
    # energy balance: supply = load + charging - unserved, every hour
    np.testing.assert_allclose(supplied, load + o["charge"] - o["unserved"], atol=1e-6)
    for s in correction.SOURCES:
        assert o[s].min() >= -1e-9, s
        cap = p["installed_mw"].get(s, 0)
        assert o[s].max() <= cap + 1e-6, f"{s} above installed {cap} MW"
    # state of charge stays within the usable energy
    eta = np.sqrt(cfg["correction"]["round_trip_efficiency"])
    emax = cfg["correction"]["bess_usable_hours"] * p.get("bess_mw", 0)
    soc = emax + np.cumsum(o["charge"] * eta - o["BESS"] / eta)
    assert soc.min() >= -1e-6 and soc.max() <= emax + 1e-6
    # charging happens only inside the scenario's window
    if p.get("bess_mw"):
        lo, hi = cfg["dispatch"]["windows_h"][p["charge_window"]]
        hour = np.tile(np.arange(24), 365)
        assert not o["charge"][(hour < lo) | (hour > hi)].any()


def test_s3_is_always_islandable(corr):
    t = corr["table15"].set_index(["year", "scenario"])["alolp_pct"]
    assert t[("mixed", "S3")] == t[("spike", "S3")] == 100.0
