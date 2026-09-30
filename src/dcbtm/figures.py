"""Figures 4, 5 and 6, drawn as the archived notebooks drew them.

Styling is copied from the notebooks so a regenerated figure can be compared with the
manuscript's. Each function reads a computed table and never recomputes the model.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .dispatch import BASELINE  # noqa: E402

# Only the PNG's text chunk would otherwise carry the matplotlib version.
PNG_META = {"Software": None}


def figure4(bands: pd.DataFrame, cfg: dict, out: Path) -> Path:
    """Monte Carlo demand bands, % of facility capacity (data_center_demand_mc.ipynb)."""
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = {"Normal Day": "blue", "High Usage (Spike)": "red", "Weekend/Batch": "green"}
    for s in cfg["demand"]["scenarios"]:
        g = bands[bands["scenario"] == s]
        ax.plot(g["hour"], g["p50_pct"], label=f"{s} (Median)", color=colors[s], linewidth=2)
        ax.fill_between(g["hour"], g["p5_pct"], g["p95_pct"], color=colors[s], alpha=0.15)
    ax.set_title("Stochastic 24-Hour Power Demand \n(Normalized Across All Scaling Phases)",
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("Hour of Day (CST)", fontsize=12)
    ax.set_ylabel("Power Demand (% of Total Facility Capacity)", fontsize=12)
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 110)
    ax.axhline(100, color="black", linestyle="--", linewidth=2, label="100% Facility Cap (25MW, 100MW, 250MW)")
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.7)
    plt.xticks(np.arange(0, 25, 2))
    plt.yticks(np.arange(0, 111, 10))
    path = out / "fig4_demand_monte_carlo.png"
    plt.savefig(path, dpi=300, bbox_inches="tight", metadata=PNG_META)
    plt.close(fig)
    return path


def figure5(results: dict[str, pd.DataFrame], cfg: dict, out: Path) -> Path:
    """Stacked dispatch, 2 x 3 panels (scenarios_gen.ipynb cell 1)."""
    subtitles = {s["title"]: s["subtitle"] for s in cfg["dispatch"]["scenarios"].values()}
    panels = {k: v for k, v in results.items() if k != BASELINE}
    fig, axes = plt.subplots(3, 2, figsize=(18, 18), sharex=True)
    plt.subplots_adjust(hspace=0.35, wspace=0.15)
    axes = axes.flatten()
    colors = {"Grid": "#aaaaaa", "Geothermal": "#8b4513", "SMR": "#4b0082", "Solar PPA": "#ffcc00",
              "RICE": "#ff6600", "Microturbines": "#d2691e", "BESS (Discharge)": "#00cc66"}
    sources = ["Geothermal", "SMR", "Grid", "Solar PPA", "RICE", "Microturbines", "BESS (Discharge)"]
    ax = axes[0]
    for idx, (title, df) in enumerate(panels.items()):
        ax = axes[idx]
        t, demand = df["hour"].to_numpy(), df["demand_mw"].to_numpy()
        ax.stackplot(t, [df[s].to_numpy() for s in sources], labels=sources,
                     colors=[colors[s] for s in sources], alpha=0.85)
        charge = df["BESS (Charge)"].to_numpy()
        if np.max(charge) > 0:
            ax.fill_between(t, 0, -charge, color="#003399", alpha=0.7, label="BESS (Charge Load)")
        ax.plot(t, demand + charge, color="red", linestyle="--", linewidth=1.5, label="Demand + Charging")
        ax.plot(t, demand, color="black", linewidth=2, label="IT Demand")
        ax.set_title(title, fontsize=13, fontweight="bold", pad=15)
        ax.text(0.5, 1.01, subtitles[title], transform=ax.transAxes, ha="center", va="bottom",
                fontsize=10, color="darkblue", style="italic")
        if idx % 2 == 0:
            ax.set_ylabel("Power (MW)")
        ax.set_xlim(0, 24)
        ax.set_ylim(-40, 280)
        ax.grid(True, linestyle=":", alpha=0.6)
        if idx >= 4:
            ax.set_xlabel("Hour of Day (CST)")
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    fig.legend(by_label.values(), by_label.keys(), loc="lower center", bbox_to_anchor=(0.5, 0.03), ncol=5, fontsize=12)
    plt.subplots_adjust(bottom=0.12)
    path = out / "fig5_scenario_dispatch.png"
    plt.savefig(path, dpi=300, bbox_inches="tight", metadata=PNG_META)
    plt.close(fig)
    return path


def figure6(t13: pd.DataFrame, out: Path) -> Path:
    """Capacity factor vs resilience reserve (utilization_rates.ipynb)."""
    fig, ax = plt.subplots(figsize=(10, 6))
    index = np.arange(len(t13))
    ax.bar(index, t13["capacity_factor_pct"], 0.55, label="Operational Capacity Factor (Active Dispatch)",
           color="#2ca02c", edgecolor="black")
    ax.bar(index, t13["resilience_reserve_pct"], 0.55, bottom=t13["capacity_factor_pct"],
           label="Resilience Reserve (N+1 Standby / Outage Bridging)", color="#98df8a", edgecolor="black")
    ax.set_ylabel("Total Physical Nameplate Capacity (%)", fontsize=12, fontweight="bold")
    ax.set_xticks(index)
    ax.set_xticklabels(t13["asset_scenario"], rotation=15, ha="right", fontsize=11)
    ax.set_ylim(0, 115)
    ax.axhline(y=100, color="red", linestyle="--", linewidth=1.5,
               label="Installed Nameplate Capacity ($P_{nameplate}$)")
    ax.legend(loc="upper right", fontsize=10, framealpha=0.9)
    ax.yaxis.grid(True, linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)
    plt.tight_layout()
    path = out / "fig6_asset_utilization.png"
    plt.savefig(path, dpi=300, metadata=PNG_META)
    plt.close(fig)
    return path
