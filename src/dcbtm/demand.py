"""Stochastic 24-hour demand: paper Section 4.3, Eqs. 1-5, Figure 4 and Table 9.

Ported from ``archive/notebooks/data_center_demand_mc.ipynb``. Expression order and
random-number consumption are kept exactly as the notebook had them, so the port agrees
with it bit for bit (``tests/test_agreement_with_archive.py``).

The draws use the legacy ``numpy.random.RandomState``, whose stream is frozen across NumPy
versions. A fresh ``RandomState(seed)`` replaces the notebook's ``np.random.seed(seed)``;
the two produce the same sequence.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def time_grid(time_steps: int) -> np.ndarray:
    """Hours 0..24 inclusive on ``time_steps`` points (the notebooks' ``np.linspace``)."""
    return np.linspace(0, 24, time_steps)


def base_utilization(scenario: str, t: np.ndarray) -> np.ndarray:
    """The deterministic diurnal baseline mu(t) of Eqs. 3-5."""
    if scenario == "Normal Day":
        u = 0.4 + 0.3 * np.sin(np.pi * (t - 6) / 12) + 0.1 * np.sin(np.pi * (t - 14) / 6)
    elif scenario == "High Usage (Spike)":
        u = 0.7 + 0.25 * np.sin(np.pi * (t - 8) / 14)
    elif scenario == "Weekend/Batch":
        u = 0.3 + 0.1 * np.sin(np.pi * (t - 12) / 12)
    else:
        raise ValueError(f"unknown demand scenario {scenario!r}")
    return np.clip(u, 0, 1)


def simulate(scenario: str, cap_mw: float, rng: np.random.RandomState, cfg: dict) -> np.ndarray:
    """Monte Carlo draws of total facility power, shape (iterations, time_steps), in MW.

    Eq. 1: P_total = [P_idle + (P_max_IT - P_idle) * U_sim] * PUE, hard-capped at cap_mw.
    Eq. 2: U_sim = clip(mu + eps, 0, 1), eps a 4-step rolling mean of N(0, volatility).
    """
    d = cfg["demand"]
    T, n = d["time_steps"], d["iterations"]
    pue, idle, vol, win = d["pue"], d["idle_fraction"], d["volatility"], d["smoothing_window"]
    max_it_power = cap_mw / pue
    base_it_power = max_it_power * idle
    mean_u = base_utilization(scenario, time_grid(T))
    sims = np.zeros((n, T))
    for i in range(n):
        noise = rng.normal(0, vol, T)
        smoothed_noise = pd.Series(noise).rolling(window=win, min_periods=1).mean().values
        u_sim = np.clip(mean_u + smoothed_noise, 0.0, 1.0)
        it_power = base_it_power + (max_it_power - base_it_power) * u_sim
        total_power = it_power * pue
        sims[i, :] = np.clip(total_power, 0, cap_mw)
    return sims


def bands(sims: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """P5, P50 and P95 across draws at each time step."""
    return tuple(np.percentile(sims, q, axis=0) for q in (5, 50, 95))


def figure4_bands(cfg: dict) -> pd.DataFrame:
    """Figure 4: normalised run (cap = 100 %), scenarios in order from one RandomState.

    This is exactly the notebook's run. Tidy output: one row per (scenario, time step).
    """
    d = cfg["demand"]
    rng = np.random.RandomState(cfg["seed"])
    t = time_grid(d["time_steps"])
    frames = []
    for s in d["scenarios"]:
        p5, p50, p95 = bands(simulate(s, d["normalised_cap"], rng, cfg))
        frames.append(pd.DataFrame({"scenario": s, "hour": t, "p5_pct": p5, "p50_pct": p50, "p95_pct": p95}))
    return pd.concat(frames, ignore_index=True)


def table9(cfg: dict) -> pd.DataFrame:
    """Table 9, RECONSTRUCTED: no notebook in the source material computes it.

    The published values are reproduced by this procedure, which is the notebook's
    simulation run in MW rather than per cent:

        one RandomState(seed); for each phase cap (outer), for each scenario (inner):
            Avg Power            = mean over time of the per-step median
            95th Percentile Peak = max over time of the per-step P95
            Min Idle Power       = min over time of the per-step P5

    The published table TRUNCATES these to one decimal in 26 of 27 cells (the 27th is
    rounded); results/reproduction_report.md lists the cell. Values here are unrounded.
    """
    d = cfg["demand"]
    rng = np.random.RandomState(cfg["seed"])
    rows = []
    for cap in d["phases_mw"]:
        for s in d["scenarios"]:
            p5, p50, p95 = bands(simulate(s, float(cap), rng, cfg))
            rows.append({"phase_mw": cap, "scenario": s, "avg_power_mw": p50.mean(),
                         "p95_peak_mw": p95.max(), "min_idle_mw": p5.min()})
    return pd.DataFrame(rows)
