"""Reproduce every table and figure, then compare them with the published paper.

    python scripts/run_all.py              # everything (Figures 1-2 need a network once)
    python scripts/run_all.py --no-maps    # offline: skips Figures 1-2 and says so

Writes results/tables/*.csv, results/figures/*.png and results/reproduction_report.md.
Takes about a minute; the Monte Carlo (12 x 1,000 draws) is most of it.
"""
from __future__ import annotations

import argparse
import sys
import time

import numpy as np
import pandas as pd

from dcbtm import demand, dispatch, figures, lcoe, resilience, scale, utilization, verify
from dcbtm.config import load_config, load_table
from dcbtm.paths import Paths

DECIMALS = 6  # written tables are rounded so they compare across platforms

# The paper includes Figures 1-2 as PDFs, so they are compared as PDFs. Rendering a PDF needs
# a library this repository does not depend on, so the comparison was measured once, on
# 2026-09-30 (PyMuPDF, 150 dpi, Windows, the environment in requirements-lock.txt), and is
# stated rather than recomputed.
MAP_NOTE = "vs archive/manuscript-figures/{pdf}, measured once 2026-09-30: {result}"


def write(df: pd.DataFrame, path) -> None:
    df.round(DECIMALS).to_csv(path, index=False, lineterminator="\n")
    print(f"  wrote {path.relative_to(path.parents[2])}  ({len(df)} rows)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-maps", action="store_true", help="skip Figures 1-2 (cartopy, needs network once)")
    args = ap.parse_args(argv)
    t0 = time.time()
    P = Paths()
    P.ensure_outputs()
    cfg = load_config(P)
    print(f"root: {P.root}")

    print("[1/6] demand Monte Carlo (Figure 4, Table 9)")
    bands = demand.figure4_bands(cfg)
    t9 = demand.table9(cfg)
    write(bands, P.tables / "fig4_demand_bands.csv")
    write(t9, P.tables / "table09_demand_monte_carlo.csv")

    print("[2/6] dispatch (Figure 5, Table 11)")
    disp = dispatch.run(cfg)
    summ = dispatch.summary(disp, cfg)
    t11 = dispatch.installed_table(cfg)
    write(dispatch.tidy(disp), P.tables / "fig5_dispatch_24h.csv")
    write(summ, P.tables / "dispatch_summary.csv")
    write(t11, P.tables / "table11_installed_capacity.csv")

    print("[3/6] LCOE (Table 12) and the Table 14 blend")
    costs = load_table("technology_costs", P)
    t12 = lcoe.lcoe_table(costs, cfg)
    write(t12, P.tables / "table12_lcoe.csv")
    published = pd.read_csv(P.published / "published_values.csv")
    pub_lcoe = {row["row"]: float(row["value"]) for row in published.to_dict("records")
                if row["item"].startswith("T12.lcoe.")}
    blend = lcoe.blended(summ, pub_lcoe)
    write(blend, P.tables / "table14_blended_lcoe_attempt.csv")

    print("[4/6] utilisation (Table 13), scale (Table 3), resilience (Table 15)")
    t13 = utilization.table13(load_table("asset_utilization", P), cfg)
    t3 = scale.table3(cfg)
    btm = resilience.max_btm_output(cfg)
    write(t13, P.tables / "table13_asset_utilization.csv")
    write(t3, P.tables / "table03_compute_scale.csv")
    write(btm, P.tables / "table15_max_btm_output.csv")

    print("[5/6] figures")
    figs = [
        {"figure": "Figure 1", "source": "maps_for_dc.ipynb (executed cell)", "file": None, "ms": None,
         "note": MAP_NOTE.format(pdf="us_texas_datacenters.pdf", result=(
             "same content; our page is 1.9 pt (0.4 %) taller, which offsets every edge by a pixel "
             "(4.3 % of pixels differ by >16 levels at 150 dpi)"))},
        {"figure": "Figure 2", "source": "maps_for_dc.ipynb (executed cell)", "file": None, "ms": None,
         "note": MAP_NOTE.format(pdf="global_datacenters.pdf", result=(
             "same page size; 0.24 % of pixels differ by >16 levels at 150 dpi"))},
        {"figure": "Figure 3", "source": "TikZ in the manuscript; not produced by code", "file": None, "ms": None},
        {"figure": "Figure 4", "source": "data_center_demand_mc.ipynb", "file": None, "ms": "demand_monte.png"},
        {"figure": "Figure 5", "source": "scenarios_gen.ipynb cell 1", "file": None, "ms": "scenario_dispatch.png"},
        {"figure": "Figure 6", "source": "utilization_rates.ipynb", "file": None,
         "ms": "internal_asset_utilization.png"},
    ]
    made = {"Figure 4": figures.figure4(bands, cfg, P.figures),
            "Figure 5": figures.figure5(disp, cfg, P.figures),
            "Figure 6": figures.figure6(t13, P.figures)}
    if args.no_maps:
        print("  !! --no-maps: Figures 1 and 2 were NOT regenerated. The committed copies are unchanged.")
    else:
        from dcbtm import maps
        made["Figure 1"] = maps.figure1(load_table("markets_us", P), P.figures)
        made["Figure 2"] = maps.figure2(load_table("markets_global", P), P.figures)
    for f in figs:
        if f["figure"] in made:
            f["file"] = f"results/figures/{made[f['figure']].name}"
            if f["ms"]:
                f["comparison"] = verify.compare_images(made[f["figure"]], P.archive / "manuscript-figures" / f["ms"])
            print(f"  wrote {f['file']}")

    print("[6/6] compare with the published paper")
    r = {"table3": t3, "tokens_per_second": scale.tokens_per_second(cfg["scale"]["tokens_facility_zettaflops"], cfg),
         "table9": t9, "table11": t11, "costs": costs, "lcoe": t12, "table13": t13, "blended": blend, "max_btm": btm}
    chk = verify.check(r, cfg, published)
    write(chk, P.tables / "reproduction_check.csv")
    extras = invariants(disp, cfg)
    verify.report(chk, figs, extras, P.results / "reproduction_report.md")
    print("  wrote results/reproduction_report.md")
    print("\n" + chk["status"].value_counts().to_string())
    print(f"\ndone in {time.time() - t0:.0f} s")
    return 0


def invariants(disp: dict[str, pd.DataFrame], cfg: dict) -> dict[str, str]:
    """Facts about the dispatch stage the report states and the tests assert."""
    out = {}
    neg = {k: float(df[dispatch.SOURCES].min().min()) for k, df in disp.items()}
    out["smallest value of any source in any scenario (MW)"] = f"{min(neg.values()):.6f}"
    over = []
    for s in cfg["dispatch"]["scenarios"].values():
        df = disp[s["title"]]
        for src in dispatch.GENERATION:
            key = "BESS" if src.startswith("BESS") else src
            cap = s["installed_mw"].get(key)
            if cap is not None and df[src].max() > cap + 1e-9:
                over.append(f"{s['title']}: {src} peaks at {df[src].max():.2f} MW > installed {cap} MW")
            if cap is None and df[src].max() > 1e-9:
                over.append(f"{s['title']}: {src} dispatches {df[src].max():.2f} MW but has no installed capacity")
    out["dispatch above installed capacity (Table 11)"] = "; ".join(over) if over else "none"
    imb = []
    for k, df in disp.items():
        gap = df[dispatch.GENERATION].sum(axis=1) - (df["demand_mw"] + df["BESS (Charge)"])
        if np.abs(gap).max() > 1e-9:
            imb.append(f"{k}: supply - (demand + charging) ranges {gap.min():.2f} to {gap.max():.2f} MW")
    out["energy balance, supply = demand + charging, every step"] = "; ".join(imb) if imb else "holds in every scenario"
    return out


if __name__ == "__main__":
    sys.exit(main())
