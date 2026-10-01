"""Things that must be true of any correct output, whatever the numbers."""
from __future__ import annotations

import re

import numpy as np
import pytest

from dcbtm import dispatch


def test_demand_bands_are_ordered_and_bounded(stages, cfg):
    b = stages["bands"]
    assert len(b) == len(cfg["demand"]["scenarios"]) * cfg["demand"]["time_steps"]
    assert (b["p5_pct"] <= b["p50_pct"]).all() and (b["p50_pct"] <= b["p95_pct"]).all()
    floor = 100 * cfg["demand"]["idle_fraction"]  # idle IT x PUE, as % of capacity
    assert b["p5_pct"].min() >= floor - 1e-9
    assert b["p95_pct"].max() <= cfg["demand"]["normalised_cap"] + 1e-9


def test_table9_statistics_are_ordered_and_capped(stages):
    t = stages["table9"]
    assert len(t) == 9
    assert (t["min_idle_mw"] <= t["avg_power_mw"]).all() and (t["avg_power_mw"] <= t["p95_peak_mw"]).all()
    assert (t["p95_peak_mw"] <= t["phase_mw"] + 1e-9).all()


def test_dispatch_is_never_negative(stages):
    for title, df in stages["dispatch"].items():
        assert df[dispatch.SOURCES].min().min() >= 0, title


def test_dispatch_meets_demand_plus_charging_every_step(stages):
    for title, df in stages["dispatch"].items():
        gap = df[dispatch.GENERATION].sum(axis=1) - (df["demand_mw"] + df["BESS (Charge)"])
        assert np.abs(gap).max() < 1e-9, f"{title}: supply misses demand by up to {np.abs(gap).max():.3g} MW"


def test_dispatch_above_installed_capacity_is_exactly_the_known_case(stages, cfg):
    """The published Figure 5 runs S6 microturbines to ~93 MW against 80 MW installed.

    That is a property of the published model, recorded in the README and the report, so
    this asserts the exceedance is exactly that one. A change that adds, removes or moves
    an exceedance fails here and must be looked at.
    """
    over = set()
    for key, s in cfg["dispatch"]["scenarios"].items():
        df = stages["dispatch"][s["title"]]
        for src in dispatch.GENERATION:
            cap = s["installed_mw"].get("BESS" if src.startswith("BESS") else src)
            peak = df[src].max()
            if (cap is None and peak > 1e-9) or (cap is not None and peak > cap + 1e-9):
                over.add((key, src))
    assert over == {("S6", "Microturbines")}
    peak = stages["dispatch"][cfg["dispatch"]["scenarios"]["S6"]["title"]]["Microturbines"].max()
    assert peak == pytest.approx(93.42, abs=0.01)


def test_bess_mwh_is_mw_times_duration(stages, cfg):
    t = stages["table11"].dropna(subset=["BESS"])
    assert (t["BESS_MWh"] == t["BESS"] * cfg["dispatch"]["bess_duration_h"]).all()
    assert len(t) == 4


def test_figure5_subtitles_state_the_installed_capacities(cfg):
    words = {"Geo": "Geothermal", "Solar": "Solar PPA", "Micro": "Microturbines"}
    for key, s in cfg["dispatch"]["scenarios"].items():
        stated = {words.get(n, n): float(mw) for n, mw in re.findall(r"(\w+) \((\d+)MW\)", s["subtitle"])}
        assert stated == {k: float(v) for k, v in s["installed_mw"].items()}, key


def test_lcoe_of_a_pure_energy_price_is_the_price(stages):
    """A PPA with no capital or O&M costs exactly its price, whatever the discounting."""
    t = stages["lcoe"].set_index("technology")["lcoe_usd_per_mwh"]
    assert t["Utility Solar PPA"] == pytest.approx(35.0, abs=1e-12)


def test_lcoe_exceeds_its_marginal_cost(stages):
    c = stages["costs"].set_index("technology")
    t = stages["lcoe"].set_index("technology")["lcoe_usd_per_mwh"]
    marginal = c["var_om_usd_per_mwh"] + c["fuel_usd_per_mwh"]
    assert (t >= marginal - 1e-12).all()


def test_capacity_factor_and_reserve_sum_to_100(stages):
    t = stages["table13"]
    assert np.allclose(t["capacity_factor_pct"] + t["resilience_reserve_pct"], 100)
    assert ((t["capacity_factor_pct"] > 0) & (t["capacity_factor_pct"] <= 100)).all()


def test_scale_is_linear_in_facility_size(stages):
    t = stages["table3"].set_index("facility_mw")
    for col in ("racks", "compute_exaflops", "fabric_petabits_s", "egress_terabits_s"):
        assert t.at[100, col] == pytest.approx(4 * t.at[25, col]) == pytest.approx(2 * t.at[50, col])
