"""Asset utilisation: paper Section 5.2.2, Eqs. 7-8, Table 13 and Figure 6.

Ported from ``archive/notebooks/utilization_rates.ipynb``.

The paper calls the dispatch column "internally derived". In the source it is an INPUT
(``data/raw/asset_utilization.csv``), set by stated duty assumptions -- full load all year
for S3 and S5, 45 % for microturbines, 30 % for RICE, 7.5 % for the BESS -- not computed
from the dispatch stage. Capacity factor and resilience reserve follow from it exactly.
"""
from __future__ import annotations

import pandas as pd


def table13(assets: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    df = assets.copy()
    df["total_possible_mwh"] = df["nameplate_mw"] * cfg["utilization"]["hours_per_year"]
    df["capacity_factor_pct"] = (df["projected_annual_mwh"] / df["total_possible_mwh"]) * 100
    df["resilience_reserve_pct"] = 100 - df["capacity_factor_pct"]
    return df
