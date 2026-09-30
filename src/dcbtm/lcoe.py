"""Technology LCOE: paper Section 4.5, Eq. 6, Table 12; and the Table 14 blend.

Ported from ``archive/notebooks/lcoe_calcs.ipynb``: a 1 MW reference plant, capital spent
in year 0, operating cost and energy discounted from year 1 to the end of life.

The published Table 12 LCOE column does NOT match what this computes for four of seven
technologies (Grid, EGS, SMR, BESS), and no single discount rate / life / capacity factor
reproduces the published column. The inputs match exactly. See the reproduction report.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

BESS = "Hybrid BESS (LCOS)"

# dispatch source -> Table 12 technology, for the energy-weighted blend
SOURCE_TO_TECH = {
    "Grid": "ERCOT Grid (345 kV)",
    "Solar PPA": "Utility Solar PPA",
    "RICE": "RICE (Natural Gas)",
    "Geothermal": "Enhanced Geothermal",
    "SMR": "Small Modular Reactor",
    "Microturbines": "Microturbines",
    "BESS (Discharge)": BESS,
}


def lcoe_table(costs: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    c = cfg["lcoe"]
    r, kw, hours = c["discount_rate"], c["reference_kw"], c["hours_per_year"]
    out = []
    for row in costs.to_dict("records"):
        if row["technology"] == BESS:
            annual_energy_mwh = c["bess_mwh_per_day"] * 365
        else:
            annual_energy_mwh = (kw / 1000) * hours * row["capacity_factor"]
        capex_total = kw * row["capex_usd_per_kw"]
        annual_op_cost = (kw * row["fixed_om_usd_per_kw_yr"]
                          + annual_energy_mwh * row["var_om_usd_per_mwh"]
                          + annual_energy_mwh * row["fuel_usd_per_mwh"])
        pv_costs, pv_energy = capex_total, 0.0
        for year in range(1, int(row["lifespan_yr"]) + 1):
            discount_factor = (1 + r) ** year
            pv_costs += annual_op_cost / discount_factor
            pv_energy += annual_energy_mwh / discount_factor
        out.append({"technology": row["technology"], "annual_energy_mwh_per_mw": annual_energy_mwh,
                    "lcoe_usd_per_mwh": pv_costs / pv_energy})
    return pd.DataFrame(out)


def blended(dispatch_summary: pd.DataFrame, lcoe_by_tech: dict[str, float]) -> pd.DataFrame:
    """Energy-weighted LCOE per scenario, as Section 4.5 describes the Table 14 method.

    NOT a reproduction of Table 14: no code in the source material computes that table,
    and the paper's method names an 8,760-hour dispatch that does not exist. This applies
    the stated method to the one day that does, so the gap can be seen rather than assumed.
    BESS charging load is not priced here (its energy is counted when discharged).
    """
    rows = []
    for scen, g in dispatch_summary.groupby("scenario", sort=False):
        g = g[g["source"].isin(SOURCE_TO_TECH)]
        e = g.set_index("source")["energy_mwh_day"]
        cost = sum(e[s] * lcoe_by_tech[SOURCE_TO_TECH[s]] for s in e.index)
        total = e.sum()
        rows.append({"scenario": scen, "energy_mwh_day": total,
                     "blended_lcoe_usd_per_mwh": cost / total if total > 0 else np.nan})
    return pd.DataFrame(rows)
