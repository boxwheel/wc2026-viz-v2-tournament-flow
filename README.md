# wc2026-viz-v2-tournament-flow

WAVE-3 rebuilds for the Tournament-Flow lane of the WC-2026 visualization
gallery. Each leaf addresses concrete rubric flaws called out in the
Wave-2 feedback nodes on the parent gallery
(https://github.com/boxwheel/wc2026-viz-tournament-flow).

## Repo layout
- `data/load.py` — tidy loaders over the Kaggle `mominullptr/fifa-world-cup-2026-dataset`.
- `style/house.py` — shared theme (palette, typography, PNG+SVG contract).
- `transforms/` — reusable computations (Elo expected-pts, etc.).
- `plots/<name>.py` — one module per viz. Each writes a PNG@200dpi and SVG into `artifacts/`.

## Wave-3 viz built so far
| Module | Proposal type | Source feedback | Fixes / improves |
|---|---|---|---|
| `plots/v10b_venues_map_fixed.py` | IMPROVE | venues map (f84b6fcc) | Real Natural-Earth basemap (not lat bands); capacity label bug fixed; top-goal venues reconciled.

## Reproduce
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install matplotlib seaborn pandas numpy geopandas adjustText highlight-text
# Kaggle dataset → fifa_data/  (see CLAUDE.md for the curl command)
python3 plots/v10b_venues_map_fixed.py
```
