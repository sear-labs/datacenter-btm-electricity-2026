# datacenter-btm-electricity-2026 conventions

The portable standard governs this repo. Read it before working here, and again before finishing:

    https://github.com/sear-labs/code-standard     canonical - same from any machine
    a local clone, if you have one                 faster; check its branch, then pull

# Part 11 - This project specifically

**Archetype A, published.** The code behind Jones Jr. and Jones Sr. (2026), *Electricity* 7(2), 43,
doi:10.3390/electricity7020043. Written in Python from the start, so it is not Archetype P;
the original notebooks are kept in `archive/` only as evidence of what produced the paper.
Name per the standard: subject, then journal and year. *Electricity* is a single-word title,
so the journal part is the word itself, as in `lithium-optsc-energies-2024`.

**The four questions, answered 2026-09-30.**
- Sensitivity: may reach a public host. Everything here is the published paper's own code and
  numbers plus public literature. No client, venture or NDA material, and none may be added:
  source only from the paper's own folders, and scan before every commit that adds files.
- Activity: finished. Corrections land on `main` by pull request; the Zenodo release is frozen.
- Syncing: none. The working tree is outside every syncing folder.
- Writers: one machine, `IE-132612`. Environment: `dev/venvs/datacenter-btm-electricity-2026`
  (conda-forge Python 3.12.14, `requirements-lock.txt`).

**Merges:** Jones Jr. merges pull requests (his instruction, 2026-09-30). Sessions open PRs
and never merge. The standard's table would also admit coauthors, if Jones Sr. is ever added
as a collaborator; that is his call, not a session's.

## What must stay true

- `python scripts/run_all.py` reproduces every table and figure and writes
  `results/reproduction_report.md`. `pytest -q` passes against the COMMITTED results, before
  `run_all.py` rewrites them (CI runs it both ways).
- `archive/` is frozen by SHA-256. Never edit it. If a file there is wrong, the fix goes in
  `src/`, and the difference is written down.
- The port agrees with the archived notebooks EXACTLY (`tests/test_agreement_with_archive.py`).
  That holds because `src/` keeps the notebooks' expression order and random-number
  consumption. "Tidying" an expression can break bit-agreement; run that test.
- `data/published/published_values.csv` is the version of record, checked value by value
  against the article page on 2026-09-30 (160 values, multiset match per table, with a
  deliberately wrong value shown to be caught). Do not edit it to make a check pass.
- The list of what does not reproduce appears three times, and `test_reproduction.py` pins it:
  the README, the report, and the test itself. Change all three or none.

## Known facts about the paper that the code cannot change

Recorded here so no session "fixes" the code to match them. The report has the numbers.
- Table 12's LCOE column is not what `lcoe_calcs.ipynb` computes for Grid, EGS, SMR and BESS.
  Same formula (RICE and microturbines match to $1/kW of CapEx), different inputs for those four;
  672 alternative conventions tried, none fits, and the inputs are not identifiable.
- Tables 14 (blended LCOE) and 15 (ALOLP): Jones Jr. computed them with code that was later lost.
  It was searched for on 2026-09-30 (README, "The missing code") and not found. If it turns up,
  archive it verbatim, run it, and move those items to REPRODUCED or DIFFERS.
- Table 9 comes from an earlier notebook version (`archive/notebooks/history/data_center_demand_mc_v2.ipynb`,
  recovered from Colab revision history 2026-10-01); the published values are truncated, not rounded.
- The paper's methods describe an 8,760-hour dispatch with state of charge, 88 % round-trip
  efficiency and ramp limits. The code is one 24-hour day with none of those.
- In S6, the published Figure 5 dispatches microturbines to 93.4 MW against 80 MW installed.
