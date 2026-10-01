"""Figures 1 and 2: market maps (maps_for_dc.ipynb, the executed "Improved" cell).

Market capacities are the authors' reading of the cited industry reports (CBRE H2 2025
for Figure 1, Cushman & Wakefield 2025 for Figure 2) and live in data/raw/markets_*.csv.
cartopy fetches Natural Earth coastlines and borders (public domain) on first use, so
this stage needs a network connection once; every other stage runs offline.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

PNG_META = {"Software": None}
PDF_META = {"Creator": None, "Producer": None, "CreationDate": None}

# Presentation only: the label text (with line breaks) and its offset in degrees.
US_LABELS = {
    "Northern Virginia": ("Northern\nVirginia", (2.0, 1.5)),
    "Silicon Valley": ("Silicon\nValley", (-3.5, -2.5)),
    "Chicago": ("Chicago", (2.0, 1.5)),
    "Atlanta": ("Atlanta", (2.5, -1.5)),
    "Phoenix": ("Phoenix", (-4.0, -2.0)),
    "Portland": ("Portland", (2.0, 1.2)),
    "Dallas-Fort Worth": ("Dallas-\nFort Worth", (3.0, 1.0)),
    "Austin": ("Austin", (-4.5, 0.0)),
    "San Antonio": ("San Antonio", (-5.5, -1.0)),
    "Houston": ("Houston", (2.5, -1.5)),
}
US_TIERS = {
    "saturated": {"color": "#8e99a4", "label": "Stable / Saturated"},
    "growth": {"color": "#4a90d9", "label": "High Growth"},
    "ercot_hyper": {"color": "#d63031", "label": "Hyper-Growth (ERCOT)"},
    "ercot_emerging": {"color": "#e17055", "label": "Emerging (ERCOT)"},
}
GLOBAL_LABELS = {
    "N. Virginia": (5, 3), "Texas (ERCOT)": (-8, -4), "W. Coast": (-10, -4), "Frankfurt": (3, 3),
    "London": (-6, 3), "Tokyo": (4, 3), "Singapore": (5, -3), "Beijing": (5, 3), "Sydney": (5, -3),
    "São Paulo": (5, -4),
}
GLOBAL_CLUSTERS = {
    "namerica": {"color": "#27ae60", "label": "North America"},
    "europe": {"color": "#2980b9", "label": "Europe (FLAP-D)"},
    "apac": {"color": "#c0392b", "label": "Asia-Pacific"},
    "emerging": {"color": "#f39c12", "label": "Emerging Markets"},
}


def figure1(markets: pd.DataFrame, out: Path) -> Path:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    proj = ccrs.AlbersEqualArea(central_longitude=-96, central_latitude=37.5, standard_parallels=(29.5, 45.5))
    fig, ax = plt.subplots(figsize=(12, 7.5), subplot_kw={"projection": proj})
    ax.set_extent([-125, -66, 24, 50], crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.OCEAN, facecolor="#f0f4f8", zorder=0)
    ax.add_feature(cfeature.LAND, facecolor="#fafafa", edgecolor="none", zorder=0)
    ax.add_feature(cfeature.STATES, edgecolor="#d0d0d0", linewidth=0.4, zorder=1)
    ax.add_feature(cfeature.BORDERS, edgecolor="#a0a0a0", linewidth=0.6, zorder=1)
    ax.add_feature(cfeature.COASTLINE, edgecolor="#a0a0a0", linewidth=0.5, zorder=1)
    ax.add_feature(cfeature.LAKES, facecolor="#f0f4f8", edgecolor="#c0c0c0", linewidth=0.3, zorder=1)
    text_effect = [pe.withStroke(linewidth=2.5, foreground="white")]
    ax.plot([-104.8, -93.5, -93.5, -104.8, -104.8], [25.8, 25.8, 36.8, 36.8, 25.8], transform=ccrs.PlateCarree(),
            color="#d63031", linewidth=2, linestyle="--", alpha=0.7, zorder=2)
    ax.text(-99.0, 37.5, "ERCOT Service Territory", transform=ccrs.PlateCarree(), fontsize=8.5, fontstyle="italic",
            fontweight="bold", color="#c0392b", ha="center", zorder=10, path_effects=text_effect)
    scale = 0.08
    for r in markets.itertuples():
        ax.scatter(r.lon, r.lat, transform=ccrs.PlateCarree(), s=r.capacity_mw * scale, c=US_TIERS[r.tier]["color"],
                   alpha=0.8, edgecolors="white", linewidths=0.8, zorder=5)
    for r in markets.itertuples():
        label, (dx, dy) = US_LABELS.get(r.market, (r.market, (2, 1)))
        is_ercot = "ercot" in r.tier
        ax.annotate(label, xy=(r.lon, r.lat), xytext=(r.lon + dx, r.lat + dy), transform=ccrs.PlateCarree(),
                    fontsize=7.5 if is_ercot else 7, fontweight="bold" if is_ercot else "normal", color="#2c3e50",
                    arrowprops=dict(arrowstyle="-", color="#999999", lw=0.6, connectionstyle="arc3,rad=0.1"),
                    path_effects=text_effect, zorder=10, annotation_clip=True)
    legend_elements = [Line2D([0], [0], marker="o", color="w", markerfacecolor=p["color"], markersize=10,
                              markeredgecolor="white", markeredgewidth=0.5, label=p["label"])
                       for p in US_TIERS.values()]
    for ref_mw in [500, 1500, 4000]:
        legend_elements.append(Line2D([0], [0], marker="o", color="w", markerfacecolor="#cccccc",
                                      markersize=np.sqrt(ref_mw * scale) * 0.85, markeredgecolor="#999999",
                                      markeredgewidth=0.4, label=f"{ref_mw} MW"))
    leg = ax.legend(handles=legend_elements, loc="lower right", fontsize=8, title="Market Trajectory", title_fontsize=9,
                    frameon=True, fancybox=True, framealpha=0.95, edgecolor="#cccccc", borderpad=1.0,
                    handletextpad=0.8, labelspacing=0.9)
    leg.get_frame().set_linewidth(0.5)
    plt.tight_layout(pad=0.5)
    path = out / "fig1_us_texas_datacenters.png"
    plt.savefig(path.with_suffix(".pdf"), bbox_inches="tight", facecolor="white", metadata=PDF_META)
    plt.savefig(path, dpi=300, bbox_inches="tight", facecolor="white", metadata=PNG_META)
    plt.close(fig)
    return path


def figure2(hubs: pd.DataFrame, out: Path) -> Path:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    fig, ax = plt.subplots(figsize=(14, 7), subplot_kw={"projection": ccrs.Robinson(central_longitude=10)})
    ax.set_global()
    ax.add_feature(cfeature.OCEAN, facecolor="#f0f4f8", zorder=0)
    ax.add_feature(cfeature.LAND, facecolor="#f5f5f5", edgecolor="none", zorder=0)
    ax.add_feature(cfeature.BORDERS, edgecolor="#d5d5d5", linewidth=0.3, zorder=1)
    ax.add_feature(cfeature.COASTLINE, edgecolor="#b0b0b0", linewidth=0.4, zorder=1)
    scale = 0.07
    for r in hubs.itertuples():
        ax.scatter(r.lon, r.lat, transform=ccrs.PlateCarree(), s=r.capacity_mw * scale,
                   c=GLOBAL_CLUSTERS[r.cluster]["color"], alpha=0.8, edgecolors="white", linewidths=0.7, zorder=5)
    text_effect = [pe.withStroke(linewidth=2, foreground="white")]
    for r in hubs.itertuples():
        if r.hub in GLOBAL_LABELS:
            dx, dy = GLOBAL_LABELS[r.hub]
            ax.annotate(r.hub, xy=(r.lon, r.lat), xytext=(r.lon + dx, r.lat + dy), transform=ccrs.PlateCarree(),
                        fontsize=6.5, color="#2c3e50", arrowprops=dict(arrowstyle="-", color="#aaaaaa", lw=0.5),
                        path_effects=text_effect, zorder=10, annotation_clip=True)
    legend_elements = [Line2D([0], [0], marker="o", color="w", markerfacecolor=p["color"], markersize=9,
                              markeredgecolor="white", markeredgewidth=0.5, label=p["label"])
                       for p in GLOBAL_CLUSTERS.values()]
    leg = ax.legend(handles=legend_elements, loc="lower left", fontsize=8, title="Data Center Cluster",
                    title_fontsize=9,
                    frameon=True, fancybox=True, framealpha=0.95, edgecolor="#cccccc", borderpad=0.8)
    leg.get_frame().set_linewidth(0.5)
    plt.tight_layout(pad=0.5)
    path = out / "fig2_global_datacenters.png"
    plt.savefig(path.with_suffix(".pdf"), bbox_inches="tight", facecolor="white", metadata=PDF_META)
    plt.savefig(path, dpi=300, bbox_inches="tight", facecolor="white", metadata=PNG_META)
    plt.close(fig)
    return path
