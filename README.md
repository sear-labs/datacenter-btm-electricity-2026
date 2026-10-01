# datacenter-btm-electricity-2026

Code and data behind **Jones Jr. and Jones Sr. (2026), "Megawatts to Zettaflops: A Techno-Economic
Framework for Grid-Tied Behind-the-Meter Architectures in AI Data Centers"**, *Electricity* 7(2), 43,
[doi:10.3390/electricity7020043](https://doi.org/10.3390/electricity7020043).

It regenerates every computed table and figure in the paper from one command, and then compares
each number with the published article and says which ones do not match.

**The authors have corrected Tables 12, 14 and 15 and some of the text.** The paper's three
conclusions are unaffected; some specific findings change. See
[Correction to the published article](#correction-to-the-published-article).

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
pytest -q                                                            # 104 tests; no solver, no licence
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
   not a reproduction. The authors' correction recomputes the table over a year (below).
3. **Table 15, ALOLP.** The code that produced it has not been found, and the paper gives no outage
   probabilities to rebuild it from. For S4, S5 and S6 the
   published value equals Max BTM Output ÷ 250 MW exactly; for S1 (72.5 vs 72.0) and S2 (91.2 vs
   98.0) it does not. That is an observation, not a reconstruction. The authors' correction
   recomputes the table from Equations (11) and (12) (below).
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

## Correction to the published article

*Jones Jr. and Jones Sr., 2026-10-01.* The three conclusions in Section 7 of the article are
unaffected by these corrections; what changes are specific findings, listed under
[Effect on the conclusions](#effect-on-the-conclusions). Several values in Tables 12, 14 and 15 do
not follow from the equations and inputs stated in the article. The authors have recomputed these
tables from the article's own equations and inputs, and have corrected two arithmetic errors and
three references, as set out below. Every corrected number is computed by `scripts/run_all.py`
(`src/dcbtm/correction.py`), and `tests/test_correction.py` checks this section against it.

**Summary of the errors**

1. **Table 12.** The calculated LCOE for four technologies (ERCOT Grid, Enhanced Geothermal, Small
   Modular Reactor, Hybrid BESS) was not computed from the capital costs printed in the same table.
2. **Table 14.** The blended LCOE values were not the result of the energy-weighted calculation
   described in Section 4.5.
3. **Table 15 and Equation (12).** The ALOLP values equal the ratio of on-site dispatchable capacity
   to the 250 MW load for three of six scenarios, rather than the result of Equations (11) and (12).
   Equation (12) is also restated so that it yields a percentage.
4. **Section 2.2.** The token throughput omitted the factor of 2 in its own equation.
5. **Table 5.** The 3-mile total did not equal the sum of its rows.
6. **References.** One cited article has since been retracted, one reference was attached to a
   statement it does not support, and one title was incorrect.
7. **Sections 4.4 and 5.2.2.** The description of the dispatch simulation and of Table 13 is
   corrected to match the calculations performed.

### Table 12

The Calc. LCOE column was not computed from the capital costs printed beside it for four
technologies. Recomputed with Equation (7), the stated 8 % discount rate and the lifespans in
Table 10, it reads as below. All inputs, and the other columns, are unchanged.

| Technology | Calc. LCOE, published ($/MWh) | Calc. LCOE, corrected ($/MWh) |
|---|---|---|
| ERCOT Grid (345 kV) | 76.71 | 77.31 |
| Utility Solar PPA | 35.00 | 35.00 |
| RICE (Natural Gas) | 60.27 | 60.25 |
| Enhanced Geothermal | 68.61 | 61.85 |
| Small Modular Reactor | 93.24 | 98.32 |
| Microturbines | 79.62 | 79.63 |
| Hybrid BESS (LCOS) | 88.58 | 85.50 |

### Table 14

The blended LCOE values were estimates and did not result from the calculation Section 4.5
describes. They are recomputed as that section states: the sum, over technologies, of each
technology's LCOE (corrected Table 12) multiplied by its share of the energy supplied over a
representative 8,760-hour year.

The year is built from the Monte Carlo demand model of Section 4.3, Equations (2)–(6), at hourly
resolution: weekdays follow the Normal Day profile, weekends the Weekend/Batch profile, and 10 % of
weekdays the High Usage (Spike) profile. Each scenario is dispatched with the merit order and
installed capacities of Table 11, with battery state of charge, 88 % round-trip efficiency and a
4-hour usable discharge (Table 10). Battery discharge is priced at its LCOS; the energy used to
charge it is priced at the source that supplied it. Installed capacity held in reserve is not
charged, consistent with Section 5.2.2.

| Scenario | Blended LCOE, published ($/MWh) | Blended LCOE, corrected ($/MWh) |
|---|---|---|
| Baseline | 75.00 | 77.31 |
| S1 (Island) | 85.50 | 72.63 |
| S2 (Hybrid PPA) | 72.40 | 54.21 |
| S3 (Geo-Long) | 68.00 | 61.85 |
| S4 (Geo + PPA) | 64.50 | 59.55 |
| S5 (Nuclear) | 94.20 | 97.42 |
| S6 (Geo + Micro) | 77.80 | 66.28 |

The column header loses "Est.". The published Baseline value, $75.00, was the grid energy price
rather than the grid LCOE. In S6 the 80 MW of microturbines cannot cover every hour the 50 MW grid
cap leaves to them, so 1,072 MWh a year (0.1 % of the load) goes unserved; the blend is taken over
the energy supplied.

As published, the ranking from cheapest was S4, S3, S2, Baseline, S6, S1, S5.

As corrected, the ranking from cheapest is S2, S4, S3, S6, S1, Baseline, S5.

### Equation (12) and Table 15

Equation (12) defined ALOLP as a difference of two probabilities, which cannot be reported as a
percentage, and the ALOLP values in Table 15 were not computed from Equations (11) and (12).
For S4, S5 and S6 they equal the ratio of on-site dispatchable capacity to the 250 MW load.
Equation (12) should read:

```math
\mathrm{ALOLP} = \left(1 - \frac{\mathrm{LOLP}_{site}}{\mathrm{LOLP}_{grid}}\right) \times 100\%
```

With grid outages independent of the IT load, as assumed in Table 10, the outage probability
cancels and ALOLP becomes the share of hours in which on-site supply alone meets the load:

```math
\mathrm{ALOLP} = \frac{100\%}{8760} \sum_{t=1}^{8760} \mathbf{1}\left[ L_{IT}(t) \le G_{BTM}(t) \right]
```

Here G_BTM(t) is the firm on-site capacity installed in Table 11 (geothermal, SMR, RICE,
microturbines), plus solar output in hour t, plus the battery discharge its state of charge allows
in hour t. The year is the representative mixed year used for Table 14.

| Scenario | ALOLP, published (%) | ALOLP, corrected (%) |
|---|---|---|
| S1: Island (RICE) | 72.5 | 88.5 |
| S2: Hybrid PPA | 91.2 | >99.9 |
| S3: 100% Geothermal | >99.9 | 100.0 |
| S4: Geo + PPA | 58.0 | 86.6 |
| S5: SMR + PPA | 72.0 | 96.5 |
| S6: Geo + Microturbines | 84.0 | 97.1 |

Max BTM Output and the other columns are unchanged.

As published, the ranking from highest ALOLP was S3, S2, S6, S1, S5, S4.

As corrected, the ranking from highest ALOLP is S3, S2, S6, S5, S1, S4; only S1 and S5 trade places.

ALOLP depends strongly on how often demand approaches its peak. In a year made only of High Usage
(Spike) days, the same calculation gives S1 34.7, S2 99.4, S3 100.0, S4 3.7, S5 45.4 and S6 58.4.
The order of the scenarios is the same in both years.

### Text corrections

- **Abstract.** The sentences "The results indicate that the blended LCOE scenario ranges from
  $64.50/MWh (Geothermal + Solar PPA) to $94.20/MWh (SMR-anchored), compared to a $75.00/MWh
  pure-grid baseline. The 100% Geothermal configuration achieves a scenario-dependent ALOLP
  exceeding 99.9%, while gas-dependent configurations range from 58.0% to 91.2%." should read: "The
  results indicate that the blended LCOE ranges from $54.21/MWh (Solar PPA + RICE) to $97.42/MWh
  (SMR-anchored), compared with $77.31/MWh for a pure-grid baseline; the lowest-cost zero-carbon
  configuration (Geothermal + Solar PPA) is $59.55/MWh. The 100% Geothermal configuration achieves a
  scenario-dependent ALOLP of 100%, while gas-dependent configurations range from 88.5% to over
  99.9%."
- **Section 2.2.** "…can theoretically generate 36.6 billion tokens per second." should read
  "…can theoretically generate 18.3 billion tokens per second." (1.1 × 10²¹ FLOP/s ÷ (2 × 30 × 10⁹)).
- **Table 5.** The Total Est. CapEx under the 3-Mile Substation Rule should read "$11 M–$25 M", the
  sum of the rows above it.
- **Section 4.4.** The sentence beginning "Ramp-rate constraints were imposed…" should read: "Ramp
  rates of RICEs (10–15% per minute) and microturbines allow full output within one hour and
  therefore do not constrain the hourly dispatch; geothermal systems and SMRs are dispatched as
  baseload up to their installed capacity." After the first sentence of Section 4.4, add: "In the
  representative year, weekdays follow the Normal Day profile, weekends the Weekend/Batch profile,
  and 10% of weekdays the High Usage (Spike) profile."
- **Figure 5 caption.** Add: "The figure illustrates the dispatch rules on one High Usage (Spike)
  day and does not apply the battery state-of-charge limit used for Tables 14 and 15. On this day
  the S6 microturbines briefly exceed their 80 MW installed capacity, by up to 13.4 MW."
- **Section 5.2.2.** "Table 13 presents the dispatch-derived utilization metrics for each physical
  BTM asset." should read: "Table 13 presents the utilization metrics implied by the projected
  annual dispatch of each physical BTM asset. The projected dispatch values are planning duty cycles
  (full output all year for the geothermal and SMR baseload, and 45%, 30% and 7.5% of hours for
  microturbines, RICE and BESS), not outputs of the dispatch simulation."
- **Section 5.3.** The sentence "When considered alongside the LCOE results in Table 14, the
  trade-space between cost and resilience becomes apparent: the lowest-LCOE configuration (S4,
  $64.50/MWh) achieves only 58.0% ALOLP, while the highest-resilience configuration (S3, >99.9%
  ALOLP) carries a moderate LCOE of $68.00/MWh." should read: "When considered alongside the LCOE
  results in Table 14, the trade-space is between cost and resilience on one side and fuel
  dependency on the other: the lowest-LCOE configuration (S2, $54.21/MWh) also exceeds 99.9% ALOLP
  but depends on a natural gas pipeline; among zero-carbon configurations, S4 has the lowest LCOE
  ($59.55/MWh) and the lowest ALOLP (86.6%), while S3 achieves the highest ALOLP (100%) at
  $61.85/MWh."
- **Section 6.** "For operational resilience, zero-carbon baseload technologies (EGS and SMR)
  demonstrated the highest ALOLP values (>99.9% and 72.0% respectively, limited by sizing
  constraints)." should read: "For operational resilience, the 100% EGS configuration achieved the
  highest ALOLP (100%); the SMR configuration reached 96.5%, limited by its 180 MW sizing."
- **References.**
  - Reference [10] (Sheng et al., *Energies* 2026, 19, 722) was retracted by the publisher on
    29 January 2026 (retraction notice doi:10.3390/en19153655). It is removed, and the citation
    "[9,10]" in Section 1.2.1 becomes "[9]".
  - In Section 1.2.3, the sentence ending "…for balancing local generation and grid interaction
    [19]." cites a reference that does not support it. The citation should be to a new reference:
    Korkas, C.D.; Baldi, S.; Kosmatopoulos, E.B. Grid-Connected Microgrids: Demand Management via
    Distributed Control and Human-in-the-Loop Optimization. In *Advances in Renewable Energies and
    Power Technologies*; Elsevier, 2018; pp. 315–344.
    https://doi.org/10.1016/B978-0-12-813185-5.00025-5. Reference [19] remains cited where it
    appears elsewhere.
  - Reference [37] should read: Fotopoulou, M.; Tsekouras, G.; Rakopoulos, D.; Kontargyri, V.
    Demand response optimization for the enhancement of the distribution system's operation.
    *Sustain. Energy Grids Netw.* **2025**, *44*, 102051.
- **Data Availability Statement.** The article says "No new data were created." The code and data
  that reproduce its figures and tables, including these corrections, are in this repository.

### Effect on the conclusions

The three enumerated conclusions in Section 7 stand. Two findings in the Abstract and Sections 5.3
and 6 change: the lowest-cost configuration is S2 rather than S4, and the trade-off is between cost
and resilience on one side and fuel dependency and carbon on the other, rather than between cost
and resilience.

| Finding | As published | As corrected | Status |
|---|---|---|---|
| Conclusion 1: BTM generation can accelerate deployment | qualitative | unchanged | Holds |
| Conclusion 2: reserve capacity as insurance; ALOLP above 99% in the strongest configurations | CF 7.5–30%, reserves >70% (Table 13); ALOLP >99% | Table 13 unchanged; S2 and S3 exceed 99.9% | Holds |
| Conclusion 3: decoupled BESS architecture | qualitative | unchanged | Holds |
| Highest-resilience configuration | S3, >99.9% | S3, 100% | Holds |
| S1 and S4 have lower ALOLP because on-site capacity is below 250 MW | 72.5% and 58.0% | 88.5% and 86.6%, the two lowest | Holds |
| Most expensive configuration | S5, $94.20 | S5, $97.42 | Holds |
| Lowest-cost zero-carbon configuration | S4 | S4, $59.55 | Holds |
| Lowest-cost configuration overall | S4, $64.50 | S2, $54.21 (gas-dependent) | Changes |
| BTM against the grid baseline | S1, S5 and S6 above the $75.00 grid | all except S5 below the $77.31 grid | Changes |
| Cost against resilience | the cheapest (S4) is the least resilient | the cheapest (S2) is among the most resilient; the trade-off is fuel dependency | Changes |
| SMR resilience | 72.0%, among the highest | 96.5%, below S2, S3 and S6 | Changes |

The overall direction of the article is unchanged: no single portfolio is best on every objective,
geothermal is the most resilient, SMR the most expensive, and behind-the-meter generation is
cost-competitive with the grid.

The authors state that the three conclusions in Section 7 are unaffected by these corrections; the
changes to specific findings are those listed above. The code and data that reproduce every figure
and table, including the corrected Tables 12, 14 and 15, are in this repository. The authors
apologize for any inconvenience caused.

## Where the code and the paper's methods differ

The code is what produced the published figures; the methods section describes more than it does.
Recorded so nobody mistakes one for the other.

- **Dispatch is one day, not a year.** The paper describes an hourly 8,760-hour dispatch with state
  of charge, 88 % round-trip efficiency and ramp limits. The code that drew Figure 5 dispatches one
  representative day on a 96-point grid by fixed rules, with none of those. The correction's
  dispatch (`src/dcbtm/correction.py`) runs the year, with state of charge and round-trip efficiency.
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
                                 resilience, figures, maps, verify; correction (the
                                 authors' correction to Tables 12, 14 and 15)
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
