"""Compare every computed number with the version of record, and say which do not match.

The published values are in ``data/published/published_values.csv``, transcribed from the
article page at doi:10.3390/electricity7020043 and checked there value by value. Each has
a tolerance of half its last displayed digit, except Table 9 (0.1 MW, because the paper
truncates rather than rounds; see :func:`dcbtm.demand.table9`).

Every item gets a KIND, which says what claim is being tested:

    computed     the code computes it; REPRODUCED or DIFFERS
    input        it is an input (data/raw or config.yaml); MATCHES or DIFFERS from the paper
    arithmetic   the paper's own rows should sum to its total; CONSISTENT or DIFFERS
    no code      nothing in the source material computes it; NO CODE. Where a best attempt
                 or an observation exists it is shown beside it, and is not a reproduction.
"""
from __future__ import annotations

import math
import platform
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np
import pandas as pd

STATUS = {
    "computed": ("REPRODUCED", "DIFFERS"),
    "input": ("MATCHES", "DIFFERS"),
    "arithmetic": ("CONSISTENT", "DIFFERS"),
}


def _trunc1(x: float) -> float:
    return math.floor(x * 10 + 1e-9) / 10


def computed_values(r: dict, cfg: dict, published: pd.DataFrame) -> dict[str, tuple[str, float, str]]:
    """item -> (kind, value, basis)."""
    v: dict[str, tuple[str, float, str]] = {}
    pub = published.set_index("item")["value"].astype(float)

    t3 = r["table3"].set_index("facility_mw")
    for mw in (25, 50, 100):
        v[f"T3.racks.{mw}"] = ("computed", t3.at[mw, "racks"], "facility MW / 125 kW per rack")
        ef = t3.at[mw, "compute_exaflops"]
        v[f"T3.compute.{mw}"] = ("computed", ef / 1000 if mw == 100 else ef, "racks x 1.4 EFLOPS")
        pb = t3.at[mw, "fabric_petabits_s"]
        v[f"T3.fabric.{mw}"] = ("computed", pb / 1000 if mw == 100 else pb, "racks x 1.6 Pb/s")
        v[f"T3.egress.{mw}"] = ("computed", t3.at[mw, "egress_terabits_s"], "racks x 1 Tb/s")
    v["S2.2.tokens"] = ("computed", r["tokens_per_second"] / 1e9,
                        "1.1e21 FLOP/s / (2 x 30e9): the paper's own equation; 36.7 results if the 2 is dropped")

    for side in ("1mile", "3mile"):
        for end in ("low", "high"):
            total = pub[f"T5.substation.{end}.{side}"] + pub[f"T5.line.{end}.{side}"]
            v[f"T5.total.{end}.{side}"] = ("arithmetic", total, "Substation CapEx + Transmission Line, as printed")

    for row in r["table9"].itertuples():
        for col, name in (("avg_power_mw", "avg"), ("p95_peak_mw", "p95"), ("min_idle_mw", "min")):
            x = getattr(row, col)
            shown = "truncated" if abs(_trunc1(x) - pub[f"T9.{name}.{row.phase_mw}.{row.scenario}"]) < 1e-9 else (
                "rounded" if abs(round(x, 1) - pub[f"T9.{name}.{row.phase_mw}.{row.scenario}"]) < 1e-9 else "neither")
            v[f"T9.{name}.{row.phase_mw}.{row.scenario}"] = (
                "computed", x, f"reconstructed Monte Carlo (see demand.table9); published value = {shown} to 1 dp")

    for row in r["table11"].to_dict("records"):
        for k, x in row.items():
            if k != "scenario" and not (isinstance(x, float) and np.isnan(x)):
                v[f"T11.{row['scenario']}.{k}"] = ("input", float(x), "config.yaml installed_mw (BESS MWh = MW x 5 h)")

    col = {"capex": "capex_usd_per_kw", "fom": "fixed_om_usd_per_kw_yr", "vom": "var_om_usd_per_mwh",
           "fuel": "fuel_usd_per_mwh"}
    for row in r["costs"].to_dict("records"):
        tech = row["technology"]
        for short, c in col.items():
            v[f"T12.{short}.{tech}"] = ("input", float(row[c]), "data/raw/technology_costs.csv")
        v[f"T12.cf.{tech}"] = ("input", 100 * row["capacity_factor"], "data/raw/technology_costs.csv")
    for row in r["lcoe"].itertuples():
        v[f"T12.lcoe.{row.technology}"] = ("computed", row.lcoe_usd_per_mwh, "discounted cash flow, lcoe_calcs.ipynb")

    for row in r["table13"].itertuples():
        a = row.asset_scenario
        v[f"T13.nameplate.{a}"] = ("input", row.nameplate_mw, "data/raw/asset_utilization.csv")
        v[f"T13.dispatch.{a}"] = ("input", row.projected_annual_mwh,
                                  "data/raw/asset_utilization.csv (an assumption, not a dispatch output)")
        v[f"T13.possible.{a}"] = ("computed", row.total_possible_mwh, "nameplate x 8760")
        v[f"T13.cf.{a}"] = ("computed", row.capacity_factor_pct, "Eq. 9")
        v[f"T13.rr.{a}"] = ("computed", row.resilience_reserve_pct, "Eq. 10")

    blend = r["blended"].set_index("scenario")["blended_lcoe_usd_per_mwh"]
    titles = {"Baseline": "Baseline (100% Grid)",
              **{k: s["title"] for k, s in cfg["dispatch"]["scenarios"].items()}}
    for k, title in titles.items():
        v[f"T14.{k}"] = ("no code", blend[title],
                         "attempt: Table 12 published LCOEs weighted by the one-day dispatch energy")

    for row in r["max_btm"].itertuples():
        v[f"T15.maxbtm.{row.scenario}"] = ("computed", row.max_btm_output_mw,
                                           "sum of Table 11 dispatchable BTM assets (not solar, not grid)")
        v[f"T15.alolp.{row.scenario}"] = ("no code", row.share_of_critical_load_pct,
                                          "observation only: max BTM output / 250 MW")
    return v


def check(r: dict, cfg: dict, published: pd.DataFrame) -> pd.DataFrame:
    comp = computed_values(r, cfg, published)
    rows = []
    for p in published.to_dict("records"):
        item = p["item"]
        if "operand of" in str(p.get("note") or ""):
            continue  # printed values that another check sums; not claims in their own right
        if item not in comp:
            raise KeyError(f"published item {item} has no computed counterpart; add it or mark it no code")
        kind, x, basis = comp[item]
        pv, tol = float(p["value"]), float(p["tol"])
        delta = x - pv
        if kind == "no code":
            status = "NO CODE"
        else:
            ok = abs(delta) <= tol + 1e-9
            status = STATUS[kind][0 if ok else 1]
        rows.append({"item": item, "table": p["table"], "row": p["row"], "column": p["column"], "unit": p["unit"],
                     "published": pv, "computed": round(float(x), 6), "delta": round(float(delta), 6),
                     "tol": tol, "kind": kind, "status": status, "basis": basis})
    extra = set(comp) - set(published["item"])
    assert not extra, f"computed items with no published value: {sorted(extra)}"
    return pd.DataFrame(rows)


def compare_images(ours: Path, theirs: Path) -> dict:
    """Pixel comparison, for the report only. Not a test: PNGs differ across machines."""
    from PIL import Image

    a = np.asarray(Image.open(ours).convert("RGB"), dtype=np.int16)
    b = np.asarray(Image.open(theirs).convert("RGB"), dtype=np.int16)
    if a.shape != b.shape:
        return {"same_size": False, "ours": f"{a.shape[1]}x{a.shape[0]}", "theirs": f"{b.shape[1]}x{b.shape[0]}"}
    d = np.abs(a - b).max(axis=2)
    return {"same_size": True, "size": f"{a.shape[1]}x{a.shape[0]}", "mean_abs_diff": float(d.mean()),
            "pct_pixels_differing": float(100 * (d > 16).mean())}


def _versions() -> str:
    out = [f"Python {platform.python_version()} on {platform.system()} {platform.machine()}"]
    for p in ("numpy", "pandas", "matplotlib", "cartopy", "pillow"):
        try:
            out.append(f"{p} {version(p)}")
        except PackageNotFoundError:
            out.append(f"{p} (not installed)")
    return ", ".join(out)


def _fmt(x: float) -> str:
    return f"{x:,.4f}".rstrip("0").rstrip(".") if abs(x) < 1e6 else f"{x:,.0f}"


def report(chk: pd.DataFrame, figures: list[dict], extras: dict, path: Path) -> None:
    L = ["# Reproduction report", "",
         "Generated by `scripts/run_all.py`. Do not edit by hand; edit the code and re-run.", "",
         "Every computed number in the version of record (doi:10.3390/electricity7020043) is compared",
         "with what this repository computes. Published values: `data/published/published_values.csv`.",
         "Full item list: `results/tables/reproduction_check.csv`.", "",
         f"Run environment: {_versions()}.", "", "## Summary by table", "",
         "| Table | Items | " + " | ".join(["REPRODUCED", "MATCHES", "CONSISTENT", "DIFFERS", "NO CODE"]) + " |",
         "|---|---|---|---|---|---|---|"]
    for t, g in chk.groupby("table", sort=False):
        c = g["status"].value_counts()
        L.append(f"| {t} | {len(g)} | " + " | ".join(str(c.get(s, 0)) for s in
                 ["REPRODUCED", "MATCHES", "CONSISTENT", "DIFFERS", "NO CODE"]) + " |")
    c = chk["status"].value_counts()
    L += [f"| **All** | **{len(chk)}** | " + " | ".join(f"**{c.get(s, 0)}**" for s in
          ["REPRODUCED", "MATCHES", "CONSISTENT", "DIFFERS", "NO CODE"]) + " |", "",
          "## What does not reproduce", "",
          "Every item whose status is DIFFERS or NO CODE. For NO CODE, *computed* is a best attempt",
          "or an observation, labelled in *basis*; it is not a reproduction.", "",
          "| Item | Published | Computed | Delta | Status | Basis |", "|---|---|---|---|---|---|"]
    for r in chk[chk["status"].isin(["DIFFERS", "NO CODE"])].itertuples():
        L.append(f"| {r.table}: {r.row} / {r.column} | {_fmt(r.published)} | {_fmt(r.computed)} | "
                 f"{_fmt(r.delta)} | {r.status} | {r.basis} |")
    t9 = chk[chk["table"] == "Table 9"]
    shown = t9["basis"].str.extract(r"= (\w+) to 1 dp")[0].value_counts()
    L += ["", "## Table 9: how the published values were rounded", "",
          f"All {len(t9)} cells agree within 0.1 MW. Published value equals the computed value "
          f"truncated to 1 dp in {shown.get('truncated', 0)} cells, rounded in {shown.get('rounded', 0)}, "
          f"neither in {shown.get('neither', 0)}.", ""]
    for r in t9[~t9["basis"].str.contains("truncated")].itertuples():
        L.append(f"- {r.row} / {r.column}: computed {r.computed:.4f}, published {r.published}")
    L += ["", "## Figures", "",
          "Regenerated figures are in `results/figures/`; the manuscript's are in `archive/manuscript-figures/`.",
          "The pixel comparison below was measured in the run environment above. PNGs are not",
          "byte-comparable across machines (fonts, antialiasing, library versions), so this is evidence",
          "for a reader and not a test; CI checks only that each figure was regenerated.", "",
          "| Figure | Source | Regenerated | Pixel comparison with manuscript figure |", "|---|---|---|---|"]
    for f in figures:
        cmpd = f.get("comparison")
        if cmpd is None:
            txt = f.get("note") or "n/a"
        elif not cmpd["same_size"]:
            txt = f"different size: ours {cmpd['ours']}, manuscript {cmpd['theirs']}"
        else:
            txt = (f"{cmpd['size']}; mean absolute difference {cmpd['mean_abs_diff']:.2f} of 255; "
                   f"{cmpd['pct_pixels_differing']:.2f}% of pixels differ by >16 levels")
        L.append(f"| {f['figure']} | {f['source']} | {f['file'] or 'not produced'} | {txt} |")
    L += ["", "## Invariants checked on the dispatch stage", ""]
    for k, x in extras.items():
        L.append(f"- {k}: {x}")
    path.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
