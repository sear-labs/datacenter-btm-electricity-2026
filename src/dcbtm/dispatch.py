"""24-hour Phase 3 (250 MW) dispatch: paper Section 5.1, Figure 5 and Table 11.

Ported from ``archive/notebooks/scenarios_gen.ipynb`` cell 1, the cell that wrote the
published Figure 5 (byte-identical to ``archive/manuscript-figures/scenario_dispatch.png``).
The rules below keep the notebook's expression order, so the arrays agree with it bit for
bit (``tests/test_agreement_with_archive.py``).

What this stage is, stated plainly because the paper describes more:
  * ONE representative day at 15-minute resolution, from ONE draw of the demand model
    (``RandomState(seed)``, volatility 0.05, utilisation floored at 0.1).
  * A fixed merit order per scenario, with the battery charging at a flat rate in a
    fixed window and discharging at a flat rate when a threshold is crossed.
  * No state of charge, round-trip efficiency, ramp limits or 8,760-hour year. The paper's
    Section 4.4 describes those; the surviving code implements none of them.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .demand import base_utilization, time_grid

SOURCES = ["Grid", "RICE", "Solar PPA", "Geothermal", "SMR", "Microturbines", "BESS (Discharge)", "BESS (Charge)"]
GENERATION = SOURCES[:-1]  # everything but the charging load
BASELINE = "Baseline (100% Grid)"


def demand_profile(cfg: dict) -> tuple[np.ndarray, np.ndarray]:
    """(hours, demand in MW) for the dispatch day."""
    d, dm = cfg["dispatch"], cfg["demand"]
    T = dm["time_steps"]
    t = time_grid(T)
    rng = np.random.RandomState(cfg["seed"])
    mean_u = base_utilization(d["demand_scenario"], t)
    noise = rng.normal(0, d["volatility"], T)
    smoothed_noise = pd.Series(noise).rolling(window=d["smoothing_window"], min_periods=1).mean().values
    u_sim = np.clip(mean_u + smoothed_noise, d["utilization_floor"], 1.0)
    cap, pue, idle = d["facility_mw"], dm["pue"], dm["idle_fraction"]
    max_it_power = cap / pue
    base_it_power = max_it_power * idle
    demand_mw = (base_it_power + (max_it_power - base_it_power) * u_sim) * pue
    return t, np.clip(demand_mw, 0, cap)


def windows(cfg: dict, t: np.ndarray) -> dict[str, np.ndarray]:
    return {k: (t >= a) & (t <= b) for k, (a, b) in cfg["dispatch"]["windows_h"].items()}


def solar_shape(cfg: dict, t: np.ndarray) -> np.ndarray:
    """Unit solar output: a half sine over the daylight window, zero outside it."""
    a, b = cfg["dispatch"]["windows_h"]["daylight"]
    daylight = (t >= a) & (t <= b)
    curve = np.zeros(len(t))
    curve[daylight] = np.sin(np.pi * (t[daylight] - a) / (b - a))
    return curve


def _frame(t, **cols) -> pd.DataFrame:
    z = np.zeros(len(t))
    return pd.DataFrame({"hour": t, **{s: cols.get(s, z) for s in SOURCES}})


def run(cfg: dict) -> dict[str, pd.DataFrame]:
    """MW by source for the baseline and S1-S6, keyed by scenario title."""
    t, demand_mw = demand_profile(cfg)
    w = windows(cfg, t)
    solar = solar_shape(cfg, t)
    sc = cfg["dispatch"]["scenarios"]
    out = {BASELINE: _frame(t, Grid=demand_mw)}

    p = sc["S1"]
    charge = np.where(w[p["charge_window"]], p["bess_mw"], 0)
    eff = demand_mw + charge
    grid = np.minimum(eff, p["grid_cap_mw"])
    remainder = eff - grid
    discharge = np.where(w["evening_peak"] & (demand_mw > p["discharge_if_demand_above_mw"]), p["bess_mw"], 0)
    rice = remainder - discharge
    out[p["title"]] = _frame(t, Grid=grid, RICE=rice, **{"BESS (Discharge)": discharge, "BESS (Charge)": charge})

    p = sc["S2"]
    solar_gen = solar * p["solar_mw"]
    charge = np.where(w[p["charge_window"]], p["bess_mw"], 0)
    eff = demand_mw + charge
    solar_used = np.minimum(eff, solar_gen)
    grid = np.minimum(eff - solar_used, p["grid_cap_mw"])
    remainder = eff - solar_used - grid
    discharge = np.where(w["evening_peak"] & (remainder > p["discharge_if_remainder_above_mw"]), p["bess_mw"], 0)
    rice = np.maximum(remainder - discharge, 0)
    out[p["title"]] = _frame(t, Grid=grid, RICE=rice, **{"Solar PPA": solar_used,
                             "BESS (Discharge)": discharge, "BESS (Charge)": charge})

    p = sc["S3"]
    out[p["title"]] = _frame(t, Geothermal=demand_mw)

    p = sc["S4"]
    geo = np.minimum(demand_mw, p["geo_mw"])
    solar_gen = solar * p["solar_mw"]
    charge = np.where(w[p["charge_window"]], p["bess_mw"], 0)
    eff = demand_mw + charge
    solar_used = np.maximum(np.minimum(eff - geo, solar_gen), 0)
    remainder = eff - geo - solar_used
    discharge = np.where(w["evening_peak"] & (remainder > p["discharge_if_remainder_above_mw"]), p["bess_mw"], 0)
    grid = np.maximum(remainder - discharge, 0)
    out[p["title"]] = _frame(t, Grid=grid, Geothermal=geo, **{"Solar PPA": solar_used,
                             "BESS (Discharge)": discharge, "BESS (Charge)": charge})

    p = sc["S5"]
    smr = np.minimum(demand_mw, p["smr_mw"])
    remainder = demand_mw - smr
    solar_used = np.minimum(remainder, solar * p["solar_mw"])
    grid = remainder - solar_used
    out[p["title"]] = _frame(t, Grid=grid, SMR=smr, **{"Solar PPA": solar_used})

    p = sc["S6"]
    geo = np.minimum(demand_mw, p["geo_mw"])
    charge = np.where(w[p["charge_window"]], p["bess_mw"], 0)
    eff = demand_mw + charge
    grid = np.minimum(eff - geo, p["grid_cap_mw"])
    remainder = eff - geo - grid
    discharge = np.where(w["evening_peak"] & (remainder > p["discharge_if_remainder_above_mw"]), p["bess_mw"], 0)
    micro = np.maximum(remainder - discharge, 0)
    out[p["title"]] = _frame(t, Grid=grid, Geothermal=geo, Microturbines=micro,
                             **{"BESS (Discharge)": discharge, "BESS (Charge)": charge})

    for df in out.values():
        df.insert(1, "demand_mw", demand_mw)
    return out


def tidy(results: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Long format: scenario, hour, source, mw."""
    frames = []
    for title, df in results.items():
        long = df.melt(id_vars=["hour", "demand_mw"], var_name="source", value_name="mw")
        long.insert(0, "scenario", title)
        frames.append(long)
    return pd.concat(frames, ignore_index=True)


def summary(results: dict[str, pd.DataFrame], cfg: dict) -> pd.DataFrame:
    """Per scenario and source: peak MW, energy over the day, and installed MW.

    Energy is mean MW x 24 h. The 96-point grid spans 0-24 h inclusive, so its steps are
    24/95 h rather than 15 minutes; only proportions are used downstream, and the mean
    is the simplest statement that does not pretend otherwise.
    """
    installed = {s["title"]: s.get("installed_mw", {}) for s in cfg["dispatch"]["scenarios"].values()}
    rows = []
    for title, df in results.items():
        for src in SOURCES:
            key = "BESS" if src.startswith("BESS") else src
            rows.append({"scenario": title, "source": src, "peak_mw": df[src].max(),
                         "energy_mwh_day": float(df[src].mean() * 24),
                         "installed_mw": installed.get(title, {}).get(key, np.nan)})
    return pd.DataFrame(rows)


def installed_table(cfg: dict) -> pd.DataFrame:
    """Table 11 as the configuration states it, with BESS MWh = MW x duration."""
    dur = cfg["dispatch"]["bess_duration_h"]
    rows = []
    for key, s in cfg["dispatch"]["scenarios"].items():
        row = {"scenario": key, **s["installed_mw"]}
        if "BESS" in s["installed_mw"]:
            row["BESS_MWh"] = s["installed_mw"]["BESS"] * dur
        rows.append(row)
    return pd.DataFrame(rows)
