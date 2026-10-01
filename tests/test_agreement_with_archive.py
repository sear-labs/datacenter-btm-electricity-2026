"""The port agrees with the archived notebooks that produced the published results.

Each test runs the notebook's OWN code, from archive/notebooks/, in a temporary directory
(so its savefig calls land there), and compares its arrays with the package's. Agreement is
exact wherever both run the same floating-point operations on the same machine, which is
every case here: the port kept the notebooks' expression order on purpose.

Cartopy is never needed: the map notebook is parsed, not run.
"""
from __future__ import annotations

import ast
import contextlib
import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np  # noqa: E402
import pytest  # noqa: E402

from conftest import ROOT, notebook_cells  # noqa: E402

NB = ROOT / "archive" / "notebooks"


def _run(code: str, where: Path, name: str = "__notebook__") -> dict:
    import matplotlib.pyplot as plt

    ns: dict = {"__name__": name}
    with contextlib.chdir(where), contextlib.redirect_stdout(io.StringIO()) as out:
        exec(compile(code, "<archived notebook>", "exec"), ns)
    plt.close("all")
    ns["__stdout__"] = out.getvalue()
    return ns


def _literal(code: str, name: str):
    """The value of the first assignment `name = <literal>` anywhere in the code."""
    for node in ast.walk(ast.parse(code)):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"no literal assignment to {name!r} found")


def test_dispatch_matches_scenarios_gen_cell_1(tmp_path, stages):
    cells = notebook_cells(NB / "scenarios_gen.ipynb")
    assert len(cells) == 2, "scenarios_gen.ipynb changed shape; the archive test should have caught it"
    ns = _run(cells[1], tmp_path)
    ours = stages["dispatch"]
    first = next(iter(ours.values()))
    assert np.array_equal(ns["demand_mw"], first["demand_mw"].to_numpy()), "demand profile differs"
    assert list(ns["dispatch_data"]) == [k for k in ours if not k.startswith("Baseline")]
    compared = 0
    for title, data in ns["dispatch_data"].items():
        for src, arr in data.items():
            assert np.array_equal(np.asarray(arr, dtype=float), ours[title][src].to_numpy()), f"{title} / {src}"
            compared += 1
    assert compared == 6 * 8
    assert (tmp_path / "generation_dispatch_phase3_grid_capacities.png").is_file()


def test_demand_bands_match_demand_mc_notebook(tmp_path, stages, cfg):
    (code,) = notebook_cells(NB / "data_center_demand_mc.ipynb")
    ns = _run(code, tmp_path)
    ns["np"].random.seed(cfg["seed"])  # the notebook's own module-level seed, re-applied
    bands = stages["bands"]
    for s in cfg["demand"]["scenarios"]:
        p5, p50, p95 = ns["run_monte_carlo_normalized"](s)
        g = bands[bands["scenario"] == s]
        for ours, theirs, q in ((g["p5_pct"], p5, 5), (g["p50_pct"], p50, 50), (g["p95_pct"], p95, 95)):
            assert np.array_equal(ours.to_numpy(), theirs), f"{s} P{q} differs"


def test_table9_matches_demand_mc_v2(stages):
    """Table 9 comes from an EARLIER version of the demand notebook (archive/notebooks/history).

    v2 runs the same Monte Carlo in MW for each phase, phases in the outer loop, from one
    seed, and returns only P5/P50/P95; the table's three statistics are read from those.
    Run its own definitions and its own loop order, and require bit-equality.
    """
    (code,) = notebook_cells(NB / "history" / "data_center_demand_mc_v2.ipynb")
    ns: dict = {}
    exec(compile(code.split("# Plotting Execution")[0], "<archived notebook>", "exec"), ns)  # seeds 42
    theirs = [(mw, s, *ns["run_monte_carlo"](mw, s)) for mw in ns["PHASES"].values() for s in ns["SCENARIOS"]]
    ours = stages["table9"]
    assert len(theirs) == len(ours) == 9
    for (mw, s, p5, p50, p95), row in zip(theirs, ours.itertuples()):
        assert (mw, s) == (row.phase_mw, row.scenario)
        assert p50.mean() == row.avg_power_mw and p95.max() == row.p95_peak_mw and p5.min() == row.min_idle_mw, (mw, s)


def test_lcoe_matches_lcoe_notebook(tmp_path, stages):
    (code,) = notebook_cells(NB / "lcoe_calcs.ipynb")
    printed = _run(code, tmp_path, name="__main__")["__stdout__"]
    table2 = printed.split("TABLE 2")[1]
    theirs = {}
    for line in table2.splitlines():
        parts = line.rsplit(None, 1)
        if len(parts) == 2:
            try:
                theirs[parts[0].strip()] = float(parts[1])
            except ValueError:
                pass
    ours = stages["lcoe"].set_index("technology")["lcoe_usd_per_mwh"].round(2).to_dict()
    assert theirs == ours


def test_technology_costs_csv_is_the_notebook_input(stages):
    (code,) = notebook_cells(NB / "lcoe_calcs.ipynb")
    rows = _literal(code, "input_data")
    csv = stages["costs"]
    assert len(rows) == len(csv)
    names = {"CapEx ($/kW)": "capex_usd_per_kw", "Fixed O&M ($/kW-yr)": "fixed_om_usd_per_kw_yr",
             "Var O&M ($/MWh)": "var_om_usd_per_mwh", "Fuel ($/MWh)": "fuel_usd_per_mwh",
             "Cap Factor": "capacity_factor", "Lifespan (Yrs)": "lifespan_yr"}
    for nb_row, csv_row in zip(rows, csv.to_dict("records")):
        assert nb_row["Technology"] == csv_row["technology"]
        for nb_key, col in names.items():
            assert nb_row[nb_key] == pytest.approx(csv_row[col], abs=0), f"{csv_row['technology']} {col}"


def test_utilization_matches_utilization_notebook(tmp_path, stages):
    (code,) = notebook_cells(NB / "utilization_rates.ipynb")
    df = _run(code, tmp_path)["df"]
    ours = stages["table13"]
    assert list(df["Asset_Scenario"]) == list(ours["asset_scenario"])
    for nb_col, col in (("Nameplate_Capacity_MW", "nameplate_mw"), ("Projected_Annual_MWh", "projected_annual_mwh"),
                        ("Total_Possible_MWh", "total_possible_mwh"), ("Capacity_Factor_pct", "capacity_factor_pct"),
                        ("Resilience_Reserve_pct", "resilience_reserve_pct")):
        assert np.array_equal(df[nb_col].to_numpy(dtype=float), ours[col].to_numpy(dtype=float)), col


def test_map_tables_are_the_executed_map_cell(paths):
    import pandas as pd

    cells = notebook_cells(NB / "maps_for_dc.ipynb")
    executed = next(c for c in cells if "import cartopy" in c)  # the "Improved" cell, not the "Old Code" one
    us = pd.read_csv(paths.raw / "markets_us.csv")
    nb_us = [(n.replace("-\n", "-").replace("\n", " "), lat, lon, mw, tier) for n, lat, lon, mw, tier in
             _literal(executed, "markets")]
    assert nb_us == [tuple(r) for r in us.itertuples(index=False)]
    glob = pd.read_csv(paths.raw / "markets_global.csv")
    assert _literal(executed, "hubs") == [tuple(r) for r in glob.itertuples(index=False)]
