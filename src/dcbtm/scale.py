"""Compute scale: paper Section 2.2, the tokens-per-second equation and Table 3.

No notebook computes these; they are arithmetic on the per-rack figures the paper states
(GB200 NVL72: 125 kW, ~1.4 EFLOPS FP4) and on the per-rack bandwidths Table 3 implies.
Facility MW is used directly as rack power, as the table does (no PUE deduction).
"""
from __future__ import annotations

import pandas as pd


def table3(cfg: dict) -> pd.DataFrame:
    s = cfg["scale"]
    rows = []
    for mw in s["facilities_mw"]:
        racks = mw * 1000 / s["rack_kw"]
        rows.append({"facility_mw": mw, "racks": racks,
                     "compute_exaflops": racks * s["rack_exaflops_fp4"],
                     "fabric_petabits_s": racks * s["rack_fabric_pbps"],
                     "egress_terabits_s": racks * s["rack_egress_tbps"]})
    return pd.DataFrame(rows)


def tokens_per_second(zettaflops: float, cfg: dict) -> float:
    """Tokens/s = total FLOPs / (2 x N_active): the paper's own equation."""
    s = cfg["scale"]
    return zettaflops * 1e21 / (s["flops_per_parameter_per_token"] * s["active_parameters"])
