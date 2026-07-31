# TOPICAL MAP — Indian EcoPolitical Growth

_Generated 2026-07-31, commit `11dcced`. Legend: `⟶` = dependency edge, `▓` = planned (specified in `BUILD_PLAN.md`, absent from code)._

> **Honesty header — updated after Phase 1 shipped.** The ETL is now **real and executed**:
> `config/indicators.csv`, 6 scripts under `scripts/`, and both parquet outputs exist and have run
> end-to-end (4,355 rows, 64 indicators, 1789–2031, ~6s from a clean tree). Nodes A0–A3 and B1–B5 are
> built. Everything Shiny-side (A4–A8, B6, B7) is still `▓ planned ▓` — no `app.R` exists yet.
> Map C describes code that now runs; the flatten and parse steps below are copied from working scripts,
> not sketched.

Repo shape: two independent projects under one root. `google-playstore-analysis/` is a finished Python
EDA (its own `docs/TOPICAL_MAP.md`). This map covers `indian-ecopolitical-growth/` only — an R Shiny
app with a config-driven ETL. No DB, no auth, no server routes: the "backend" is four batch R scripts
and two parquet files. Product and Developer topology are therefore shallow; Map C is where substance
lives.

---

## MAP A — Product Topology

```
┌────────────────────────┐
│ A0. Indicator Config ✅ │  the only real file in the repo
│  49 rows, 11 categories │
└───────────┬────────────┘
            │ drives every downstream node
            v
┌────────────────────────┐     ┌──────────────────────────┐
│ A1. ETL Pipeline     ▓ │ ──> │ A2. Validation Report  ▓ │
│  fetch / clean / store  │     │  6 checks -> HTML         │
└───────────┬────────────┘     └──────────────────────────┘
            │
            v
┌────────────────────────┐
│ A3. Analytical Dataset ▓│  world_bank.parquet + indicator_metadata.parquet
└───────────┬────────────┘
            │
            ├──────────────────┬──────────────────┬───────────────────┐
            v                  v                  v                   v
┌────────────────────┐ ┌───────────────┐ ┌────────────────┐ ┌────────────────┐
│ A4. Explorer     ▓ │ │ A5. Govern-  ▓│ │ A6. Advanced  ▓│ │ A7. Compare   ▓│
│ pick indicator,    │ │ ance overlay  │ │ CAGR/forecast/ │ │ India vs BRICS │
│ see series         │ │ 1996+ only    │ │ correlation    │ │ (needs re-pull)│
└─────────┬──────────┘ └───────┬───────┘ └───────┬────────┘ └───────┬────────┘
          └────────────────────┴─────────────────┴──────────────────┘
                                       │
                                       v
                          ┌──────────────────────────┐
                          │ A8. Report / Download  ▓ │
                          │  render current view      │
                          └──────────────────────────┘
```

---

**[A0] Indicator Config** ✅
- What: hand-authored source of truth. 49 indicators across 11 categories; each row carries `code`, `wb_source`, `unit`.
- Where: `config/indicators.csv` (real, 50 lines incl. header).
- Docs: `BUILD_PLAN.md` §3 (why `wb_source` exists), §5 (coverage bands).
- Verified: all 49 codes hit `api.worldbank.org/v2/indicator/{code}` and resolved; all 49 return non-empty rows for `IND`.
- Edges: ⟶ A1 (drives fetch loop), ⟶ A3 (join source for category/unit), ⟶ A4–A7 (dropdown contents).

---

**[A1] ETL Pipeline** ▓
- What: fetch 49 indicators from World Bank, tidy to long format, persist as parquet.
- Where: `scripts/download_worldbank.R`, `scripts/clean_worldbank.R` — **neither exists yet**.
- Docs: `BUILD_PLAN.md` §4 (full flow).
- Edges: ⟵ A0 (config), ⟶ A2 (feeds validation), ⟶ A3 (writes dataset).

---

**[A2] Validation Report** ▓
- What: 6 checks (dupes, year range, numeric sanity, dead codes, coverage regression, interior gaps) → HTML.
- Where: `scripts/validate.R` → `docs/validation_report.html` — neither exists.
- Docs: `BUILD_PLAN.md` §4, §5.
- **Design constraint from real data:** Gini/poverty have 8 observations across 45 years. Gaps here are *the data*, not a defect — checks 5 and 6 must warn, never fail. A naive "no missing years" check fails 4 of 49 indicators on day one.
- Edges: ⟵ A1.

---

**[A3] Analytical Dataset** ▓
- What: two parquet files — long fact table + generated metadata table.
- Where: `data_processed/world_bank.parquet`, `data_processed/indicator_metadata.parquet`.
- Docs: `BUILD_PLAN.md` §4 (schema), "Why long format" note.
- Size estimate: 49 × ~50 avg observations ≈ 2,500 rows. Small enough to load fully into Shiny memory — no lazy reads, no DB.
- Edges: ⟵ A1, ⟶ A4/A5/A6/A7.

---

**[A4] Indicator Explorer** ▓ · **[A5] Governance Overlay** ▓ · **[A6] Advanced Analytics** ▓ · **[A7] Comparison** ▓
- What: the four Shiny surfaces. A4 is the baseline (pick indicator → time series). A5 dual-axis econ vs WGI. A6 CAGR / decade / correlation / forecast. A7 multi-country.
- Where: `app.R` + `R/mod_*.R` — none exist.
- Docs: `BUILD_PLAN.md` §2 Phase 3–7.
- **A5 hard limit:** governance series start 1996. Any econ×governance correlation runs on n≈29 — too small for a confident claim, so the UI must show n alongside r.
- **A7 blocker:** dataset is `IND` only by decision. Requires a config change + re-fetch before this node can exist.
- Edges: ⟵ A3, ⟶ A8.

---

**[A8] Report / Download** ▓
- What: export current view as HTML/PDF + raw CSV.
- Where: not scoped beyond `BUILD_PLAN.md` §7 `US-009`.
- Edges: ⟵ A4–A7.

---

## MAP B — Developer Topology

```
┌──────────────────────┐
│ B0. R runtime      ▓ │  ⚠ NOT INSTALLED — `which R` -> not found
│  R + arrow + shiny    │     every B-node below is unexecutable today
└──────────┬───────────┘
           │
           v
┌──────────────────────┐        ┌───────────────────────────┐
│ B1. Config contract ✅│ ────> │ B2. WB API client       ▓ │
│  csv schema:          │        │  URL builder + retry      │
│  code|wb_source|unit  │        │  branches on wb_source    │
└──────────┬───────────┘        └────────────┬──────────────┘
           │                                  │
           │                                  v
           │                     ┌───────────────────────────┐
           │                     │ B3. Tidy layer          ▓ │
           │                     │  json -> long tibble      │
           │                     └────────────┬──────────────┘
           │                                  v
           │                     ┌───────────────────────────┐
           └───────join─────────>│ B4. Parquet store       ▓ │
                                 │  arrow::write_parquet     │
                                 └────────────┬──────────────┘
                                              │
                     ┌────────────────────────┼────────────────────────┐
                     v                        v                        v
        ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
        │ B5. Validation   ▓ │   │ B6. Shiny modules ▓│   │ B7. CI refresh   ▓ │
        │  rmarkdown render  │   │  mod_*.R + bslib   │   │  GH Action cron    │
        └────────────────────┘   └────────────────────┘   └────────────────────┘
```

---

**[B0] R Runtime** ▓ — **hard blocker, flagged honestly**
- What: R ≥ 4.3 plus `shiny`, `httr2`, `jsonlite`, `dplyr`, `tidyr`, `arrow`, `readr`, `rmarkdown`, `plotly`, `bslib`, `DT`.
- Where: no `renv.lock`, no `DESCRIPTION`, no install script.
- **Verified absent:** `which R` and `which Rscript` both return nothing on this machine.
- Consequence: per your decision, Phase 1 scripts get written **without ever being executed**. Expect a debug pass on first run — likely candidates are `arrow` needing a source build on macOS, and `httr2` API surface differences.
- Edges: ⟶ every node B1–B7.

---

**[B1] Config Contract** ✅
- What: the CSV schema every script agrees on. Five columns, no more.
- Where: `config/indicators.csv`.
- **Drift risk (the highest-value seam in this repo):** three separate consumers read this file — the fetch loop, the join in cleaning, and the Shiny dropdowns. Adding a column is safe; renaming one breaks all three silently. Any schema change must be grepped across `scripts/` and `app.R` together.
- Edges: ⟶ B2 (loop source), ⟶ B4 (join), ⟶ B6 (dropdowns).

---

**[B2] World Bank API Client** ▓
- What: build URL, GET, retry, persist raw JSON.
- Where: `scripts/download_worldbank.R` — does not exist.
- **Non-obvious requirement, verified this session:** the URL is *not* uniform. Standard indicators use the default source; the 6 governance indicators require `&source=3` **and** a `GOV_WGI_` code prefix. Without the source param the API returns HTTP 200 with an empty payload — a silent failure that looks like "India has no governance data". This is exactly why `wb_source` is a config column and not a hardcoded constant.
- Verified endpoints:
  - `.../v2/sources/2/country/IND/series/{43 codes};/data?per_page=20000` → 2,838 rows, 43 series, 34KB, 0.43s
  - `.../v2/sources/3/country/IND/series/{6 codes};/data?per_page=20000` → 156 rows, 6 series, 2KB, 0.29s
  - `.../v2/country/IND/indicator/RL.EST?format=json` → **200 OK, 0 rows** (the trap)
  - `.../v2/country/IND/indicator/A;B` → `Invalid value` — the *legacy* path takes only one code
- **Deliberately not built:** rate limiter, parallel pool, request queue, backoff ladder. Two requests
  do not justify any of it. `req_retry(max_tries = 3)` is the whole resilience story.
- gzip measured on the worst case (all countries, one indicator): 3,675,128 B → 211,142 B, **17×**.
- Edges: ⟵ B1, ⟶ B3.

---

**[B3] Tidy Layer** ▓ · **[B4] Parquet Store** ▓
- What: B3 flattens WB's nested JSON (`indicator.id`, `country.id`, `date`, `value`) into `code|year|value`; B4 joins config metadata and writes two parquet files.
- Where: `scripts/clean_worldbank.R`, `scripts/merge_sources.R` — neither exists.
- **Type trap:** on the batch endpoint the year arrives as `"YR2025"` inside a nested `variable` array, and `value` as JSON `null`. Strip the `YR` prefix and coerce to integer, or every year becomes `NA` (and a string year sorts lexically — "10" before "9"). `value` must land as `double` with `NA`, never `"NULL"` as text. See Map C1 for the exact flatten.
- Edges: ⟵ B2, ⟵ B1 (join), ⟶ B5, ⟶ B6.

---

**[B5] Validation** ▓ · **[B6] Shiny Modules** ▓ · **[B7] CI Refresh** ▓
- What: B5 renders the report; B6 is the app; B7 is a scheduled re-fetch.
- Where: `scripts/validate.R`, `app.R` + `R/mod_*.R`, `.github/workflows/` — none exist.
- Docs: `BUILD_PLAN.md` §2 Phase 3, 8.
- Edges: ⟵ B4.

---

## MAP C — Per-feature backend processing

All flows are `▓ planned ▓` — no R file exists. Paths and function names below are the *contract* Phase 1
must implement, so the map and the code start aligned rather than drifting from day one.

### C1 — Indicator fetch (the only flow with real verified behavior)

**Batched, not looped.** The `sources/{id}/series/A;B;C/data` endpoint takes a semicolon-delimited
code list, so the whole dataset is 2 requests, not 49. Measured: 0.72s total, 36KB gzipped, 2,346
non-null observations, all 49 series present.

```
config/indicators.csv
   │ readr::read_csv() |> split(~ wb_source)
   v
2 groups:  source=2 (43 codes, url len 668)   source=3 (6 codes)
   │
   ├── paste(code, collapse=";")
   │      v
   │   httr2::request(".../v2/sources/{id}/country/IND/series/{codes}/data")
   │      |> req_url_query(format="json", per_page=20000)
   │      |> req_headers(`Accept-Encoding`="gzip")
   │      |> req_retry(max_tries=3)  |> req_perform()
   │      │
   │      ├── 200 + N series == length(codes)  ─> flatten
   │      ├── 200 + 0 series  ─> stop()  [silent-empty trap — never log-and-continue]
   │      └── !=200 after 3   ─> stop() with failing URL
   │
   └── writeLines(raw) -> data_raw/source_{id}.json      [2 files, gitignored]
   v
dplyr::bind_rows -> data_raw/worldbank_raw.rds
```

**Response shape is NOT the classic v2 shape.** The batch endpoint nests dimensions in a `variable`
array — there is no top-level `date` or `indicator.id`. Flattening must pivot on `concept`:

```r
# each row: {"variable":[{concept:"Country",id:"IND"},
#                        {concept:"Series", id:"FP.CPI.TOTL.ZG"},
#                        {concept:"Time",   id:"YR2025"}], "value": 2.39884954182294}
tibble(
  code  = map_chr(variable, ~ .x$id[.x$concept == "Series"]),
  year  = as.integer(sub("YR", "", map_chr(variable, ~ .x$id[.x$concept == "Time"]))),
  value = as.numeric(value)
)
```

Note `Time` arrives as `"YR2025"`, not `"2025"` — the `sub("YR", "")` is mandatory or every year
becomes `NA`.

Shared with C2/C3: `read_indicator_config()` — one loader, three callers. Do **not** re-read the CSV
independently in `app.R`; that is how B1's drift risk becomes a bug.

### C2 — Clean & persist

```
data_raw/worldbank_raw.rds
   │
   ├── mutate(year = as.integer(date), value = as.numeric(value))
   ├── left_join(config, by = "code")        -> category, indicator, unit
   ├── filter(!is.na(value)) ; arrange(code, year)
   │
   ├──> arrow::write_parquet -> data_processed/world_bank.parquet
   └──> group_by(code) |> summarise(first_year, last_year, n_obs, pct_coverage)
          └──> arrow::write_parquet -> data_processed/indicator_metadata.parquet
```

`indicator_metadata` is **derived, never hand-written** — it is the only honest record of what the API
actually returned on a given day.

### C3 — Validate & report

```
world_bank.parquet + indicator_metadata.parquet
   │
   ├── check_duplicates(code, year)        -> FAIL if n > 0
   ├── check_year_range(1960, this_year)   -> FAIL if n > 0
   ├── check_numeric(is.finite)            -> FAIL if n > 0
   ├── check_dead_codes(n_obs == 0)        -> WARN, list codes
   ├── check_coverage_regression(vs §5)    -> WARN if n_obs dropped
   └── check_interior_gaps()               -> REPORT only  [sparse != broken]
   v
rmarkdown::render -> docs/validation_report.html
```

---

## Cross-map bridges

| Product node | Runs on | Key seam to check when touching it |
|---|---|---|
| A0 Config | B1, C1 | Column rename breaks fetch loop + join + dropdowns simultaneously. Grep `scripts/` and `app.R` together — no exceptions. |
| A1 ETL | B2, B3, C1, C2 | `wb_source` branch. Drop it and governance silently returns 0 rows with HTTP 200 — no error, just an empty chart. |
| A2 Validation | B5, C3 | Sparse-vs-broken distinction. A strict gap check fails Gini, poverty, literacy, and central-govt-debt on a healthy run. |
| A3 Dataset | B4, C2 | `year` as integer, `value` as double. String `year` sorts lexically and silently scrambles every x-axis. |
| A5 Governance | B2, C1 | 1996 start vs 1960 econ start. Any join/correlation must state n, not just r. |
| A7 Comparison | B2, C1 | Dataset is `IND`-only by decision. This node cannot exist until the country list is widened and re-fetched. |
| A4–A8 (all UI) | B0, B6 | **R is not installed.** Nothing in B6 has ever run. Treat the first `Rscript` as a debugging session, not a smoke test. |

---

## Maintenance

- Registered in `docs/PREFACTOR.md` — pending (no PREFACTOR file for this project yet; the one in `google-playstore-analysis/docs/` covers the other project only).
- **Regenerate after Phase 1 lands.** At that point roughly 60% of the `▓` markers should burn off, and Map C should be rewritten from real exported function names rather than the planned contract above.
