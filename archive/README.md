# archive/ — what produced the published paper, frozen

**Never edit anything here.** These files are the evidence of what produced the numbers and
figures in Jones Jr. and Jones Sr. (2026), doi:10.3390/electricity7020043. A correction goes
in `src/dcbtm/` and the divergence is recorded; the archive stays as it was, because its job is
to say what the paper did, not to be right.

`tests/test_archive_frozen.py` recomputes `MANIFEST.sha256` and fails if any file here changes,
disappears, or is added. `.gitattributes` marks this folder `-text`, so no platform rewrites
line endings on checkout (which would change the hashes on Windows only).

The maintained implementation is `src/dcbtm/`. `tests/test_agreement_with_archive.py` executes
these notebooks' own code and asserts that the package agrees with it exactly.

## notebooks/

Copied byte for byte from the authors' Google Drive (`01-Research/Data Center/Data Center Paper/`)
on 2026-09-30. Only the filenames changed, to remove spaces.

| File | Original name | Last modified | Produced |
|---|---|---|---|
| `scenarios_gen.ipynb` | `Scenarios_Gen.ipynb` | 2026-03-03 | Figure 5, from **cell 1**. Cell 0 is an earlier 7-panel version of the same dispatch with older titles; it did not produce a published figure. |
| `data_center_demand_mc.ipynb` | `Data Center Demand MC.ipynb` | 2026-03-03 | Figure 4 (saved as `demand_monte_carlo_normalized.png`, renamed `demand_monte.png` in the manuscript). **Its saved output is stale:** it shows the LCOE tables from `LCOE Calcs.ipynb`, not anything this cell prints. Table 9 comes from its earlier version in `history/`. |
| `lcoe_calcs.ipynb` | `LCOE Calcs.ipynb` | 2026-03-03 | The Table 12 inputs. Its computed LCOE column differs from the published one for four technologies; see `results/reproduction_report.md`. |
| `utilization_rates.ipynb` | `Utilization Rates.ipynb` | 2026-03-05 | Table 13 and Figure 6. |
| `maps_for_dc.ipynb` | `Maps for DC.ipynb` | 2026-04-01 | Figures 1 and 2, from the cell headed "Improved Claude Code". The cell headed "Old Code" was never executed in this notebook (no execution count). |

All five ran on Google Colab: Python 3.12, numpy 2.0.2, pandas 2.2.2, matplotlib 3.10.0,
cartopy 0.25.0, as recorded by the install cell of `maps_for_dc.ipynb`.

### notebooks/history/

Earlier versions of two of the notebooks above, downloaded by Jones Jr. from their Colab revision
history on 2026-10-01, byte for byte. Two further revisions, the empty "Untitled" notebooks each
started as, are not kept.

| File | Is an earlier version of | Produced |
|---|---|---|
| `data_center_demand_mc_v2.ipynb` | `data_center_demand_mc.ipynb` | **Table 9.** Runs the Monte Carlo in MW for each phase (25, 100, 250 MW), phases outer, one seed. `tests/test_agreement_with_archive.py` runs its code and gets the repository's Table 9 bit for bit. |
| `data_center_demand_mc_v3.ipynb` | `data_center_demand_mc.ipynb` | **Figure 4.** Same code as the final notebook; its saved output is the figure, where the final notebook's is a stale LCOE printout. |
| `scenarios_gen_v2.ipynb` | `scenarios_gen.ipynb` | Nothing published. An earlier dispatch on the "Normal Day" profile that the first submission's text describes, without battery charging. Its saved output is a syntax error from an earlier run. |

## manuscript-figures/

The figure files from the final manuscript source (`2026_Megawatts_to_Zettaflops_Datacenters_v3.zip`,
2026-04-01), byte for byte.

| File | Paper | Note |
|---|---|---|
| `us_texas_datacenters.pdf` | Figure 1 | The manuscript includes the PDF. |
| `global_datacenters.pdf` | Figure 2 | The manuscript includes the PDF. |
| `demand_monte.png` | Figure 4 | |
| `scenario_dispatch.png` | Figure 5 | Byte-identical (SHA-256) to `generation_dispatch_phase3_grid_capacities.png`, the output of `scenarios_gen.ipynb` cell 1. |
| `internal_asset_utilization.png` | Figure 6 | |

Figure 3 is a TikZ diagram in the manuscript and was never a file.

**Two files from that zip are deliberately NOT here:** `us_texas_datacenters.png` and
`global_datacenters.png`. They are stale outputs of the never-executed "Old Code" map cell
(a CartoDB basemap, "Portland/Hillsboro"), the manuscript does not include them, and the
published article shows the PDF versions. Keeping them would put a figure the paper never
showed beside the ones it did.
