# PREFACTOR — Documentation Map

_Generated: 2026-07-14, commit 4d4841f. Repo shape: solo data-analysis project (1 notebook-script, 1 dataset, 2 PDF write-ups, 1 README) — not a product/frontend/backend-service codebase. Most of the standard 16-leaf tree doesn't apply here; sections below are marked `n/a` where the leaf has no equivalent in a repo this shape, rather than forced to fit. Re-verify if the repo grows past a single analysis script._

## Index
| # | Segment | Files | Status |
|---|---|---|---|
| 1 | Feature Definitions | 0 | n/a |
| 2 | Feature Roadmap & Prioritization | 1 | gap (one-liner only) |
| 3 | Process & Decision Flow | 0 | n/a |
| 4 | Metrics & Success Criteria | 0 | n/a |
| 5 | Usage Guides | 1 | ok |
| 6 | Limitations & FAQ | 0 | gap |
| 7 | Onboarding | 1 | ok |
| 8 | Ongoing Operations & Support | 0 | n/a |
| 9 | Component Reference | 0 | n/a |
| 10 | Styling & Theming | 0 | n/a |
| 11 | API Contracts Consumed | 0 | n/a |
| 12 | State & Data Flow | 0 | n/a |
| 13 | Domain & Business Logic | 1 | ok |
| 14 | Data & Schema | 1 | gap (no standalone reference) |
| 15 | Queries Exposed | 0 | n/a |
| 16 | Mutations Exposed | 0 | n/a |

## 5. User > Client > Features > Usage Guides

### 1. Reference
| File | Covers | Status |
|---|---|---|
| `README.md` | What the repo is, how to run the Playstore analysis | ok |

### 2. Patterns to learn
- README is the single entry point — no separate docs site.
- Script is a `# %%` cell notebook (Jupyter/VS Code interactive), read top-to-bottom, not a CLI.

### 3. Cross-segment check
- See **13. Domain & Business Logic** (`Google Playstore Analysis.py`) — usage guide's description of "what it does" must match the actual cell sequence.

## 6. User > Client > Features > Limitations & FAQ

### 1. Reference
| File | Covers | Status |
|---|---|---|
| — | No dedicated doc found — gap | gap |

### 2. Patterns to learn
- N/A — no FAQ doc exists yet; not load-bearing at current repo size.

### 3. Cross-segment check
- See **13. Domain & Business Logic** for known data caveats (missing values, currency skew) that would belong here if this section grows.

## 7. User > Client > Workflow > Onboarding

### 1. Reference
| File | Covers | Status |
|---|---|---|
| `README.md` | Setup: clone, install deps, download dataset via `opendatasets`, open script as notebook | ok |

### 2. Patterns to learn
- Dataset download line (`od.download(...)`) is commented out after first run — one-time step, not re-run each session.

### 3. Cross-segment check
- See **14. Data & Schema** — onboarding must name the correct CSV path (`google-playstore-apps/Google-Playstore.csv`).

## 13. Developer > Backend > Functionality Pipelines > Domain & Business Logic

### 1. Reference
| File | Covers | Status |
|---|---|---|
| `Google Playstore Analysis.py` | Full EDA pipeline: load → clean → engineer → visualize, 745 lines, cell-based | ok |
| `Google Play Store analysis.pdf` | Rendered notebook output (charts + narrative) | ok |
| `Understanding Mobile Applications Marketspace - Google Play Store Data Analysis.pdf` | Write-up / findings summary | ok |

### 2. Patterns to learn
- Cleaning order matters: drop nulls on `App Name`/`Rating`/`Rating Count` before deriving anything downstream — later cells assume a null-free subset.
- Unit-normalizing helpers (`convert_m_to_kb`, `convert_k_to_numeric`, `convert_g_to_numeric`) are applied sequentially to the same column, each one only touching the suffix it targets — order-dependent, don't reorder.
- `App Id` is the de-facto primary key (unique, non-null); `App Name` is not.

### 3. Cross-segment check
- See **14. Data & Schema** (`Google-Playstore.csv`) — any new cleaning step must match actual column dtypes/values, not assumed ones.

## 14. Developer > Backend > Functionality Pipelines > Data & Schema

### 1. Reference
| File | Covers | Status |
|---|---|---|
| `Google-Playstore.csv` | Raw source data, 24 columns (App Name, Category, Rating, Installs, Size, Minimum Android, Released, Content Rating, …) | gap — no standalone column-reference doc, schema only discoverable by opening the file |

### 2. Patterns to learn
- `Installs` and `Minimum Installs` are redundant (verified equal in-script) — `Installs` is dropped, keep using `Minimum Installs`.
- `Size` is mixed-unit text (`M`/`k`/`G`/`Varies with device`) — must go through the three convert_* helpers before it's numeric.

### 3. Cross-segment check
- See **13. Domain & Business Logic** — every schema quirk listed here has a corresponding cleaning cell; don't add a new quirk note without also checking whether the script already handles it.

---
**Gaps worth closing, in priority order:** a short column-reference doc for the CSV (14), since it's currently only discoverable by reading the script or opening the file directly.

**Related map:** `docs/TOPICAL_MAP.md` — ASCII flowcharts of product/dev/processing topology, cross-referenced with this file.
