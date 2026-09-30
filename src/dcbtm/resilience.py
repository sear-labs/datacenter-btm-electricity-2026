"""Resilience: paper Section 4.6, Eqs. 9-10, Table 15.

No code in the source material computes ALOLP. Eq. 9 sums, over 8,760 hours, the
probability that IT load exceeds grid plus BTM capacity; nothing implements it, and no
outage model exists. What CAN be reproduced is the "Max BTM Output" column: it is the sum
of each scenario's dispatchable on-site capacity in Table 11 (everything but solar and
the grid, BESS included). This module computes that, and the ratio of it to the critical
load, which the report sets beside the published ALOLP column as an observation only.
"""
from __future__ import annotations

import pandas as pd


def max_btm_output(cfg: dict) -> pd.DataFrame:
    keep = set(cfg["resilience"]["dispatchable_btm"])
    load = cfg["resilience"]["critical_load_mw"]
    rows = []
    for key, s in cfg["dispatch"]["scenarios"].items():
        mw = sum(v for k, v in s["installed_mw"].items() if k in keep)
        rows.append({"scenario": key, "max_btm_output_mw": mw, "share_of_critical_load_pct": 100 * mw / load})
    return pd.DataFrame(rows)
