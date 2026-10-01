# datacenter-btm-electricity-2026

Code and data behind **Jones Jr. and Jones Sr. (2026), "Megawatts to Zettaflops: A Techno-Economic
Framework for Grid-Tied Behind-the-Meter Architectures in AI Data Centers"**, *Electricity* 7(2), 43,
[doi:10.3390/electricity7020043](https://doi.org/10.3390/electricity7020043).

It regenerates every computed table and figure in the paper from one command, and then compares
each number with the published article and says which ones do not match.

## How to cite

Cite the paper. GitHub's "Cite this repository" button reads `CITATION.cff`.

```bibtex
@article{jones2026megawatts,
  author  = {Jones, Jr., Erick C. and Jones, Sr., Erick C.},
  title   = {{Megawatts to Zettaflops: A Techno-Economic Framework for Grid-Tied Behind-the-Meter Architectures in AI Data Centers}},
  journal = {Electricity},
  year    = {2026},
  volume  = {7},
  number  = {2},
  pages   = {43},
  doi     = {10.3390/electricity7020043}
}
```

## Run it

Python 3.11–3.13. About 20 seconds.

```bash
git clone https://github.com/sear-labs/datacenter-btm-electricity-2026.git
cd datacenter-btm-electricity-2026
pip install -r requirements-lock.txt && pip install -e . --no-deps   # the exact versions that ran
python scripts/run_all.py                                            # every table and figure
pytest -q                                                            # 80 tests; no solver, no licence
```

`pip install -e ".[dev]"` instead installs the newest versions within the ranges in
`pyproject.toml`. Figures 1 and 2 need `cartopy` to download Natural Earth outlines once;
`python scripts/run_all.py --no-maps` runs everything else offline and says what it skipped.

## What reproduces

`results/reproduction_report.md` compares all 153 computed numbers in the paper with this code.
Published values are in `data/published/published_values.csv`, transcribed from the article page
and checked there value by value.

| | Items | Result |
|---|---|---|
| Table 3, compute scale | 12 | all reproduce |
| Table 9, Monte Carlo demand | 27 | all reproduce, from the original code (within 0.1 MW; see below) |
| Table 11, installed capacity | 23 | inputs; all match |
| Table 12, technology costs and LCOE | 42 | 35 inputs match; **6 of 7 LCOEs differ** |
| Table 13, asset utilisation | 25 | all reproduce |
| Table 15, Max BTM Output | 6 | all reproduce |
| Figures 1, 2, 4, 5, 6 | 5 | all regenerate; 4–6 are pixel-identical to the manuscript's on the authors' machine |

**What does not reproduce.** This list is pinned by `tests/test_reproduction.py`, so it cannot
change without the test changing too.

1. **Table 12, LCOE.** The inputs match exactly, but the computed column does not: Grid 77.31
   (published 76.71), EGS 61.85 (68.61), SMR 98.32 (93.24), BESS 85.50 (88.58), RICE 60.25 (60.27),
   microturbines 79.63 (79.62). Only solar (35.00) agrees. The formula is not the difference: RICE
   and microturbines need their printed capital cost to within $1/kW to give the published values.
   Grid, EGS, SMR and BESS instead need about $98, $5,130, $7,000 and $1,300/kW against the printed
   $150, $4,500, $7,500 and $1,250. So the published column was computed with the same formula from
   different inputs for those four technologies than the table prints. 672 alternative conventions
   (discount rate, timing, escalation, lifetimes) were also tried; none reproduces the column. Which
   inputs were used cannot be recovered: for EGS, nine different combinations fit exactly.
2. **Table 14, blended LCOE.** The code that produced it has not been found. Applying the method the
   paper describes (Table 12 LCOEs weighted by dispatched energy) to the one simulated day gives
   different numbers; `results/tables/table14_blended_lcoe_attempt.csv` shows them as an attempt,
   not a reproduction.
3. **Table 15, ALOLP.** The code that produced it has not been found, and the paper gives no outage
   probabilities to rebuild it from. For S4, S5 and S6 the
   published value equals Max BTM Output ÷ 250 MW exactly; for S1 (72.5 vs 72.0) and S2 (91.2 vs
   98.0) it does not. That is an observation, not a reconstruction.
4. **Section 2.2, tokens per second.** The paper's own equation, 1.1 × 10²¹ FLOP/s ÷ (2 × 30 × 10⁹),
   gives 18.3 billion tokens/s; the text says 36.6 billion, which is what results without the 2. The
   figure was carried over from an AI-assisted draft of 2 March 2026.
5. **Table 5, 3-mile total.** The printed rows sum to $11–25 M; the total says $12–27 M.

**How Table 9 was produced.** By an earlier version of the demand notebook, recovered from its Colab
revision history (`archive/notebooks/history/data_center_demand_mc_v2.ipynb`). It runs the Monte Carlo
in MW from one random stream seeded 42, phases in the outer loop, and returns only the per-step 5th,
50th and 95th percentiles; the table reads the mean of the median, the maximum of the 95th and the
minimum of the 5th from them. A test runs that notebook's own code and gets the repository's Table 9
bit for bit. The published values are these **truncated** to one decimal in 26 of 27 cells.

## The missing code

Tables 12 (the four LCOEs above), 14 and 15 were computed with code that was later lost. On
2026-09-30 it was searched for by reading the contents of every notebook and script in the authors'
personal and lab Google Drives, UT Arlington OneDrive, and local disks (about 120,000 code files),
for the published values and for the paper's vocabulary, with a positive control each time; and the
authors' Claude chat history was searched from within Claude. On 2026-10-01 the authors recovered the
Colab revision histories of the demand and dispatch notebooks and the Overleaf projects; those found
Table 9's code (above) and an earlier dispatch (below), but not these. The earliest draft has four
scenarios with round LCOEs ($65-$105/MWh) and ALOLP as an outage risk (0.1-2.5 %); the published
values first appear in the first submission (5 March 2026) and never change after it. If the code
turns up, it goes into `archive/` verbatim, and these items move to REPRODUCED or DIFFERS.

## Where the code and the paper's methods differ

The code is what produced the published figures; the methods section describes more than it does.
Recorded so nobody mistakes one for the other.

- **Dispatch is one day, not a year.** The paper describes an hourly 8,760-hour dispatch with state
  of charge, 88 % round-trip efficiency and ramp limits. The code dispatches one representative day
  on a 96-point grid by fixed rules, with none of those.
- **The dispatch day uses different noise.** Eq. 3 clips utilisation at 0 with the Monte Carlo's
  volatility (0.15). The dispatch day uses volatility 0.05 and a floor of 0.1 (`config.yaml`, marked).
- **Table 13's dispatch column is an input.** The paper calls it internally derived; in the code it
  is a duty assumption per asset (`data/raw/asset_utilization.csv`), from which capacity factor and
  reserve follow exactly.
- **S6 exceeds its installed microturbines.** In the published Figure 5, microturbines peak at
  93.4 MW against the 80 MW Table 11 installs. `tests/test_invariants.py` pins this as the only
  such case.
- **Figure 5's demand day changed.** The first submission says the dispatch follows a "Normal Day".
  An earlier dispatch notebook did (`archive/notebooks/history/scenarios_gen_v2.ipynb`, no battery
  charging); the published Figure 5 uses the High Usage (Spike) day with charging windows.

## Layout

    config.yaml                  every parameter; each line says which notebook it came from
    data/raw/                    input tables (costs, utilisation, map markets)
    data/published/              the paper's numbers, as published, with tolerances
    src/dcbtm/                   the model: demand, dispatch, lcoe, utilization, scale,
                                 resilience, figures, maps, verify
    scripts/run_all.py           the one entry point
    results/tables/              every computed table, and reproduction_check.csv
    results/figures/             Figures 1, 2, 4, 5, 6
    results/reproduction_report.md
    archive/                     the original notebooks and manuscript figures, frozen; see its README
    tests/                       agreement with the archive, invariants, reproduction, guards
    references.bib               the paper's 71 references, audited against doi.org

## What is committed, deliberately

`results/` is committed so a reader can see every output without running anything. That is only
safe because `tests/test_reproduction.py` fails when the committed tables and the code disagree,
and CI runs the tests against the committed results before regenerating them. Figures are
regenerated in CI but not compared there: a PNG drawn on a Linux runner is never byte-identical to
one drawn on another machine. The pixel comparison in the report was measured once and says so.

`archive/` is committed and frozen: it is the evidence of what produced the paper.

The third-party reports the authors worked from are not redistributed; `references.bib` cites them.

## Figures

- **Figure 1** (`fig1_us_texas_datacenters`). Map of US data-center markets, sized by capacity:
  Northern Virginia largest; Dallas–Fort Worth, Austin, San Antonio and Houston inside a dashed
  ERCOT box.
- **Figure 2** (`fig2_global_datacenters`). World map of hyperscale hubs by region, largest in
  Northern Virginia, Texas, the US West Coast and Beijing.
- **Figure 4** (`fig4_demand_monte_carlo`). Median and 5–95 % band of demand over 24 hours for three
  scenarios: in the spike scenario the upper band reaches 100 % of capacity from about 11:40 to 18:10
  and the median peaks at 96 %; the normal day's median peaks at 73 % mid-afternoon; the weekend
  median stays between 36 % and 52 %.
  Numbers: `results/tables/fig4_demand_bands.csv`.
- **Figure 5** (`fig5_scenario_dispatch`). Six panels of stacked generation meeting a 250 MW
  spike-day demand, one per scenario, with battery charging drawn below zero. Numbers:
  `results/tables/fig5_dispatch_24h.csv`.
- **Figure 6** (`fig6_asset_utilization`). For five assets, the share of nameplate capacity used
  (geothermal 83 %, SMR 90 %, microturbines 45 %, RICE 30 %, battery 7.5 %) and held in reserve.
  Numbers: `results/tables/table13_asset_utilization.csv`.

Figure 3 is a diagram drawn in the manuscript's LaTeX, not produced by code.

## Environment

The published figures were made on Google Colab with Python 3.12, numpy 2.0.2, pandas 2.2.2,
matplotlib 3.10.0 and cartopy 0.25.0. This port ran on Python 3.12.14 with those same versions;
`requirements-lock.txt` is the full resolved list. The random draws use NumPy's legacy
`RandomState`, whose stream is frozen across NumPy versions.

## Licence

| Path | Licence |
|---|---|
| `src/`, `scripts/`, `tests/`, `archive/notebooks/`, `config.yaml`, `pyproject.toml`, `.github/` | MIT (`LICENSE`) |
| `data/`, `results/`, `archive/manuscript-figures/`, `references.bib`, and the prose (`*.md`) | CC BY 4.0 (`LICENSE-DATA`) |

The paper is published open access by MDPI under CC BY 4.0.

## Corrections

Open a pull request against `main`. The cited version is a tagged release and does not change;
a correction becomes a new release, and you are credited in its notes and in `CITATION.cff`.
