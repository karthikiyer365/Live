# Google Play Store — Marketspace Analysis

2.3M+ apps, one CSV, no assumptions. A cell-by-cell walk from raw Kaggle export to
clean findings on what actually drives ratings, installs, and app survival on the
Play Store.

📄 [`Google Playstore Analysis.py`](./Google%20Playstore%20Analysis.py) — the pipeline, runnable as a Jupyter/VS Code cell notebook
📊 [Analysis PDF](./Google%20Play%20Store%20analysis.pdf) · [Write-up PDF](./Understanding%20Mobile%20Applications%20Marketspace%20-%20Google%20Play%20Store%20Data%20Analysis.pdf) — rendered output + narrative

## Quickstart

```bash
pip install opendatasets numpy pandas matplotlib seaborn scikit-learn tabulate plotly

# first run only — downloads the dataset, then comment this line back out
python -c "import opendatasets as od; od.download('https://www.kaggle.com/datasets/gauthamp10/google-playstore-apps')"

# open Google Playstore Analysis.py as a notebook (VS Code / Jupyter both read the `# %%` cells)
```

## The pipeline

```
Google-Playstore.csv  (2.3M rows × 24 cols)
   │
   v
┌─────────────┐     ┌──────────────────┐     ┌────────────────────┐     ┌───────────────┐
│  Ingest     │ ──> │  Clean            │ ──> │  Engineer           │ ──> │  Visualize     │
│  read_csv   │     │  drop nulls,      │     │  Year/Month/App Age │     │  20+ charts:   │
│             │     │  unit-normalize   │     │  Has_PrivacyPolicy  │     │  histograms,   │
│             │     │  Size (M/K/G),    │     │  has_dev_website    │     │  treemap,      │
│             │     │  dedupe Installs  │     │  rounded Android ver│     │  pie, boxen    │
└─────────────┘     └──────────────────┘     └────────────────────┘     └───────────────┘
```

Full column-by-column breakdown, function names, and line numbers: [`docs/TOPICAL_MAP.md`](./docs/TOPICAL_MAP.md#map-c--per-feature-backend-processing).

## What the data says

| Signal | Finding |
|---|---|
| Currency | 99.95% of listings priced in USD — everything else is noise |
| Category | Education alone accounts for ~20% of all apps |
| Ratings | Most rated apps sit between 3.5–5.0; a huge share have zero ratings at all |
| Install volume | Long tail — most apps land in the 10–10,000 install range |
| Million+ reviews | Only 829 of 2M+ apps clear a million ratings — and Action leads that club |
| Update trend | App updates peaked in 2020 |

## Repo map

| File | What it is |
|---|---|
| `Google Playstore Analysis.py` | The full EDA pipeline — clean, engineer, visualize |
| `Google-Playstore.csv` | Raw source data (Kaggle: gauthamp10/google-playstore-apps) |
| `Google Play Store analysis.pdf` | Rendered notebook output |
| `Understanding Mobile Applications Marketspace...pdf` | Narrative write-up of findings |
| `docs/TOPICAL_MAP.md` | ASCII flowcharts — product, dev, and per-cell processing topology |
| `docs/PREFACTOR.md` | Doc coverage map — what's documented, what's a gap |

---
*Built while re-learning Python's data-science stack — pandas, seaborn, plotly — on a real, messy, 2M-row dataset.*
