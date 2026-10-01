"""The authors' correction to Tables 12, 14 and 15 (README, "Correction").

Not a reproduction. The published Tables 14 and 15 were computed by code that was not found
(see :mod:`dcbtm.verify`); this module recomputes all three tables from the paper's own
equations and stated inputs, as the authors decided on 2026-10-01:

  Table 12  Eq. 7 with the capital costs printed in Table 12 (= :func:`dcbtm.lcoe.lcoe_table`).
  Table 14  Section 4.5: blended LCOE = sum over sources of (corrected Table 12 LCOE x that
            source's share of the energy it supplies), over a representative 8,760-hour year.
            Battery discharge is priced at its LCOS; the energy that charged it at the source
            that supplied it. Capacity held in reserve is not charged (Section 5.2.2).
  Table 15  Eqs. 11-12, with Eq. 12 restated as a relative reduction,
            ALOLP = (1 - LOLP_site / LOLP_grid) x 100 %. With grid outages independent of the
            IT load the outage probability cancels, leaving the share of hours in which
            on-site supply alone meets the load.

The year is built from the Section 4.3 demand model at hourly resolution (one Monte Carlo
path per day, the 15-minute steps averaged to hours). Mixed year: weekdays Normal Day,
weekends Weekend/Batch, a share of weekdays High Usage (Spike). Spike year: every day
High Usage (Spike), the day Figure 5 draws; it is reported as a sensitivity.

Each scenario is dispatched with Figure 5's merit order and thresholds (:mod:`dcbtm.dispatch`),
now capped at Table 11's installed capacity, with battery state of charge, the round-trip
efficiency split evenly between charging and discharging, and a usable discharge of
``bess_usable_hours`` x MW (Table 10: a 5-hour system at 80 % depth of discharge).
"""
from __future__ import annotations

import copy

import numpy as np
import pandas as pd

from . import demand

SOURCES = ["Grid", "Solar PPA", "RICE", "Geothermal", "SMR", "Microturbines", "BESS"]
TECH = {  # dispatch source -> Table 12 technology
    "Grid": "ERCOT Grid (345 kV)",
    "Solar PPA": "Utility Solar PPA",
    "RICE": "RICE (Natural Gas)",
    "Geothermal": "Enhanced Geothermal",
    "SMR": "Small Modular Reactor",
    "Microturbines": "Microturbines",
    "BESS": "Hybrid BESS (LCOS)",
}
SPIKE, NORMAL, WEEKEND = "High Usage (Spike)", "Normal Day", "Weekend/Batch"
# The last source each scenario calls on, after baseload, solar, capped grid and battery
# (Figure 5's rules; S3 has none).
FILLER = {"S1": "RICE", "S2": "RICE", "S4": "Grid", "S5": "Grid", "S6": "Microturbines"}


def hourly_year(kind: str, cfg: dict) -> np.ndarray:
    """8,760 hourly loads in MW for a 'mixed' or 'spike' year, from a fresh RandomState(seed).

    Each day is one draw of :func:`dcbtm.demand.simulate` at the Phase 3 capacity. In the
    mixed year a weekday is a spike day when a uniform draw falls below the configured share;
    that draw is taken before the day's demand draws.
    """
    c = cfg["correction"]
    one = copy.deepcopy(cfg)
    one["demand"]["iterations"] = 1
    cap = float(cfg["dispatch"]["facility_mw"])
    steps = cfg["demand"]["time_steps"] // 24
    rng = np.random.RandomState(cfg["seed"])
    days = []
    for d in range(c["days"]):
        if kind == "spike":
            s = SPIKE
        elif kind == "mixed":
            if d % 7 < c["weekdays_per_week"]:
                s = SPIKE if rng.rand() < c["spike_weekday_share"] else NORMAL
            else:
                s = WEEKEND
        else:
            raise ValueError(f"unknown year {kind!r}")
        days.append(demand.simulate(s, cap, rng, one)[0].reshape(24, steps).mean(axis=1))
    return np.concatenate(days)


def _hour_masks(cfg: dict, n: int) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    hour = np.tile(np.arange(24), n // 24)
    a, b = cfg["dispatch"]["windows_h"]["daylight"]
    solar = np.where((hour >= a) & (hour <= b), np.sin(np.pi * (hour - a) / (b - a)), 0.0)
    w = {k: (hour >= lo) & (hour <= hi) for k, (lo, hi) in cfg["dispatch"]["windows_h"].items()}
    return solar, w


def dispatch_year(key: str, load: np.ndarray, cfg: dict) -> dict[str, np.ndarray]:
    """Hourly MW by source for one scenario, plus 'charge', 'unserved' and 'btm_available'.

    'btm_available' is G_BTM(t) of Eq. 11: firm on-site capacity installed (Table 11), plus
    solar that hour, plus the discharge the battery's state of charge allows.
    """
    c = cfg["correction"]
    p = cfg["dispatch"]["scenarios"][key]
    inst = p["installed_mw"]
    eta = np.sqrt(c["round_trip_efficiency"])
    solar_shape, w = _hour_masks(cfg, len(load))
    firm = sum(v for k, v in inst.items() if k in c["firm_btm"])
    filler = FILLER.get(key)
    n = len(load)
    out = {k: np.zeros(n) for k in SOURCES + ["charge", "unserved", "btm_available"]}
    bmw = p.get("bess_mw", 0)
    emax = c["bess_usable_hours"] * bmw
    soc = emax  # the year starts with the battery full
    for h in range(n):
        demand_mw = load[h]
        sol = solar_shape[h] * p.get("solar_mw", 0)
        charge = min(bmw, (emax - soc) / eta) if bmw and w[p["charge_window"]][h] else 0.0
        eff = demand_mw + charge
        base = 0.0
        if key == "S3":
            base = min(eff, inst["Geothermal"])
            out["Geothermal"][h] = base
        elif "geo_mw" in p:
            base = min(demand_mw, p["geo_mw"])
            out["Geothermal"][h] = base
        elif "smr_mw" in p:
            base = min(demand_mw, p["smr_mw"])
            out["SMR"][h] = base
        rem = eff - base
        solar_used = min(rem, sol)
        out["Solar PPA"][h] = solar_used
        rem -= solar_used
        grid = min(rem, p["grid_cap_mw"]) if "grid_cap_mw" in p else 0.0
        rem -= grid
        discharge = 0.0
        if bmw and w["evening_peak"][h]:
            if "discharge_if_demand_above_mw" in p:
                trigger = demand_mw > p["discharge_if_demand_above_mw"]
            else:
                trigger = rem > p["discharge_if_remainder_above_mw"]
            if trigger:
                discharge = min(bmw, soc * eta, rem)
        rem -= discharge
        fill = 0.0
        if filler:
            fill = max(min(rem, inst.get(filler, np.inf) - (grid if filler == "Grid" else 0.0)), 0.0)
        rem -= fill
        out["Grid"][h] = grid + (fill if filler == "Grid" else 0.0)
        if filler and filler != "Grid":
            out[filler][h] = fill
        out["BESS"][h] = discharge
        out["charge"][h] = charge
        out["unserved"][h] = max(rem, 0.0)
        soc = soc + charge * eta - discharge / eta
        out["btm_available"][h] = firm + sol + min(bmw, soc * eta)
    return out


def run(cfg: dict, lcoe_table: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Corrected Tables 12, 14 and 15, and an annual energy summary, for both years."""
    lc = lcoe_table.set_index("technology")["lcoe_usd_per_mwh"]
    price = {s: float(lc[TECH[s]]) for s in SOURCES}
    keys = list(cfg["dispatch"]["scenarios"])
    t14, t15, energy = [], [], []
    for kind in ("mixed", "spike"):
        load = hourly_year(kind, cfg)
        t14.append({"year": kind, "scenario": "Baseline", "blended_lcoe_usd_per_mwh": price["Grid"]})
        for k in keys:
            o = dispatch_year(k, load, cfg)
            e = {s: float(o[s].sum()) for s in SOURCES}
            supplied = sum(e.values())
            t14.append({"year": kind, "scenario": k,
                        "blended_lcoe_usd_per_mwh": sum(e[s] * price[s] for s in SOURCES) / supplied})
            t15.append({"year": kind, "scenario": k,
                        "alolp_pct": 100 * float(np.mean(load <= o["btm_available"] + 1e-9))})
            energy.append({"year": kind, "scenario": k, "load_mwh": float(load.sum()),
                           "charge_mwh": float(o["charge"].sum()), "unserved_mwh": float(o["unserved"].sum()),
                           **{f"{s}_mwh": e[s] for s in SOURCES}})
    t12 = lcoe_table[["technology", "lcoe_usd_per_mwh"]].copy()
    return {"table12": t12, "table14": pd.DataFrame(t14), "table15": pd.DataFrame(t15),
            "energy": pd.DataFrame(energy)}
