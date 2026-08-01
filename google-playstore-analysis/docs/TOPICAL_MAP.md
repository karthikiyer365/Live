# TOPICAL MAP

_Generated: 2026-07-14, commit 4d4841f. Legend: `⟶` = dependency edge, `▓` = planned/aspirational (claimed, not in code)._

Repo shape: one active deliverable (a Google Play Store EDA pipeline), no services/routes/DB — so
Product and Developer topology collapse to a short chain. Map C (backend processing) is where the
actual substance lives: a 745-line cell-based cleaning → feature-engineering → visualization pipeline.

## MAP A — Product Topology

```
┌─────────────────┐     ┌──────────────────────┐     ┌───────────────────────────┐
│ A0. Raw Dataset  │──>  │ A1. Playstore EDA     │──>  │ A2. Write-up / Findings   │
│ (Kaggle CSV)     │     │     Pipeline (script) │     │     (2 PDFs)              │
└─────────────────┘     └──────────────────────┘     └───────────────────────────┘
                                    │
                                    v
                          ┌──────────────────────┐
                          │ A3. README (entry     │  ▓ stale — still links to
                          │     point / onboarding)│     4 deleted files
                          └──────────────────────┘
```

**[A0] Raw Dataset**
- What: 2.3M-row Google Play Store apps export, 24 columns, downloaded via Kaggle.
- Where: `Google-Playstore.csv`.
- Docs: `docs/PREFACTOR.md` §14 (gap — no column reference doc).
- Edges: ⟶ A1 (sole input).

---

**[A1] Playstore EDA Pipeline**
- What: Cleans, engineers, and visualizes the dataset end-to-end; only active "feature" in the repo.
- Where: `Google Playstore Analysis.py` (745 lines, `# %%` cell format).
- Docs: `docs/PREFACTOR.md` §13 (ok).
- Edges: ⟵ A0 (reads CSV) ⟶ A2 (its output is the PDFs).

---

**[A2] Write-up / Findings**
- What: Rendered notebook output + narrative conclusions (currency skew, rating distribution, Android version spread).
- Where: `Google Play Store analysis.pdf`, `Understanding Mobile Applications Marketspace - Google Play Store Data Analysis.pdf`.
- Docs: none dedicated — findings live only in PDF + inline script comments.
- Edges: ⟵ A1.

---

**[A3] README**
- What: Repo entry point — currently describes a 5-file "learning path" (Python 101, Nested Data Structures, Rock Paper Scissors, Market Sentiments API, Events Scraper) of which 4 files were deleted in the last commit (`4d4841f`, "rearrange files and repurpose repo").
- Where: `README.md`.
- Docs: this is the doc — flagged stale here, rewritten as part of this pass.
- Edges: ⟶ A1 (should point here, currently doesn't).

## MAP B — Developer Topology

```
┌───────────────┐   ┌────────────────┐   ┌─────────────────────┐   ┌──────────────────┐
│ B0. Ingestion  │──>│ B1. Cleaning   │──>│ B2. Feature          │──>│ B3. Visualization │
│ (opendatasets, │   │ (null drops,   │   │     Engineering      │   │ (matplotlib,      │
│  pd.read_csv)  │   │  unit parsing) │   │ (derived columns)    │   │  seaborn, plotly) │
└───────────────┘   └────────────────┘   └─────────────────────┘   └──────────────────┘
```

**[B0] Ingestion**
- What: One-time Kaggle pull (`opendatasets`) + CSV load into a single DataFrame.
- Where: `Google Playstore Analysis.py` lines 18–24.
- Docs: `docs/PREFACTOR.md` §7 (onboarding — matches).
- Edges: ⟶ B1.

---

**[B1] Cleaning**
- What: Drops nulls (`App Name`, `Rating`, `Rating Count`, `Developer Id/Email`, `Currency`, `Minimum Android`); normalizes `Size` from mixed `M/k/G/Varies with device` text to numeric KB via three sequential helpers (`convert_m_to_kb`, `convert_k_to_numeric`, `convert_g_to_numeric`); dedupes `Installs` vs `Minimum Installs` and drops the redundant one.
- Where: `Google Playstore Analysis.py` lines 62–260.
- Docs: `docs/PREFACTOR.md` §13–14.
- Edges: ⟵ B0 ⟶ B2 (engineered columns depend on cleaned `Size`/`Released`/`Minimum Android`).

---

**[B2] Feature Engineering**
- What: Derives `Year Released`, `Month Released`, `App Age`, `Has_PrivacyPolicy`, `has_developer_website`, and a rounded `Minimum Android` version (`extract_and_round_up`).
- Where: `Google Playstore Analysis.py` lines 390–428, 573–576, 652–665.
- Docs: `docs/PREFACTOR.md` §13.
- Edges: ⟵ B1 ⟶ B3 (every chart below groups by one of these derived columns).

---

**[B3] Visualization**
- What: ~20 charts — category histograms, rating distributions, install proportions, release-year trends, content-rating treemap, currency pie chart, Android-version bar/grouped-bar charts.
- Where: `Google Playstore Analysis.py` lines 276–719 (interleaved with B1/B2 cells).
- Docs: `docs/PREFACTOR.md` §13; rendered results in A2 (PDFs).
- Edges: ⟵ B2 (terminal node — no further processing downstream).

## MAP C — Per-feature backend processing

**C1. Playstore EDA pipeline (the only feature)**

```
Google-Playstore.csv
   │  pd.read_csv (line 23)
   v
df  ──> df.isna().sum() / df.describe()   [exploration, lines 29-53]
   │
   │  dropna: App Name, Rating, Rating Count      (lines 63, 70-71)
   v
df_clean
   │
   ├──> Size: str -> KB                            (convert_m/k/g_to_numeric, lines 163-224)
   ├──> Installs vs Minimum Installs: verify equal -> drop Installs   (lines 82-91)
   ├──> Minimum Android: extract_and_round_up       (line 652-662)
   ├──> Currency: dropna, distribution check         (lines 103-120)
   ├──> Released: to_datetime, fillna(median) -> Year/Month/App Age   (lines 385-398)
   ├──> Privacy Policy: fillna -> Has_PrivacyPolicy  (lines 424-428)
   ├──> Developer Website: notna -> has_developer_website  (line 573)
   └──> Content Rating: relabel (Mature 17+ -> 17+, etc.)  (lines 500-502)
   │
   v
plt/sns/px calls (20+ charts, lines 276-719)  ──> rendered inline (script) / exported (PDFs)
```

- Entry point: `Google-Playstore.csv` read at line 23 — no CLI args, no config, single hardcoded path.
- Shared helpers reused across the flow: `convert_m_to_kb` / `convert_k_to_numeric` / `convert_g_to_numeric` (each called once, order-dependent — must run M→K→G since each mutates the same column in place); `splice_string` (generic slice helper, used once for `Year Last Updated`).
- No persistence layer — output is chart windows + the two PDFs in A2; nothing writes back to disk from the script itself.
- No test/assert coverage on the cleaning functions (`convert_*`, `extract_and_round_up`, `splice_string`) — correctness is currently verified only by print-statement spot checks (e.g. lines 177, 202, 223).

## Cross-map bridges

| Product node | Runs on (B/C nodes) | Key seam to check |
|---|---|---|
| A1. Playstore EDA Pipeline | B0→B1→B2→B3, C1 | Cleaning order in C1 is order-dependent (Size unit parsing, Installs dedup) — reordering cells breaks downstream columns silently. |
| A2. Write-up / Findings | B3, C1 (chart outputs) | PDFs are a point-in-time export — if the script or CSV changes, PDFs go stale with no regeneration step tracked anywhere. |
| A3. README | A1 | README currently describes files that no longer exist (see A3 card) — highest-priority drift in the repo. |

---
Registered in `docs/PREFACTOR.md` maintenance — this file is the canonical topology map; regenerate rather than patch if the pipeline's cell structure changes materially.
