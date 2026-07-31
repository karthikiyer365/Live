# BUILD PLAN — Understanding Indian EcoPolitical Growth Over the Years

_Written 2026-07-31. Locked via grill. Every World Bank code below was hit against the live API this session — coverage numbers are measured, not assumed._

## 1. Overview

An R Shiny dashboard tracing India's economic and governance trajectory from 1960 to today, built on 49 World Bank indicators pulled through a config-driven ETL. The problem: most "India dashboard" portfolio projects hardcode a handful of indicators, break when an API key expires, and show GDP charts anyone can get from Google. This one is driven entirely by a CSV config (add a row, get a new indicator), runs on a zero-key public API, and pairs the economic series with the Worldwide Governance Indicators — the political half of "EcoPolitical" that most dashboards skip.

The architecture that emerged from grilling: **one config file feeds everything**. `config/indicators.csv` drives the download loop, the validation thresholds, and the Shiny dropdowns. No indicator name is ever typed twice.

---

## 2. Story So Far

### Phase 0 — Repo split ✅ merged
- 🗂️ Google Play Store analysis moved to `google-playstore-analysis/` (code, data, 2 PDFs, its own docs)
- 🗂️ This project scaffolded at `indian-ecopolitical-growth/`
- 📄 Root `README.md` rewritten as multi-project index

### Phase 1 — Data acquisition & ETL ✅ complete
_Full pipeline runs clean → validated in **6 seconds**. R 4.6.1 installed via `brew install r`._
- ✅ 51 candidate WB indicator codes validated against live API
- ✅ 2 dead codes found and dropped (see Key Decisions)
- ✅ 6 governance codes found to be renamed + on a separate DB — schema consequence absorbed
- ✅ Batch endpoint found — whole WB dataset in 2 calls, not 49
- ✅ IMF WEO + V-Dem promoted into Phase 1; multi-country parity verified
- ✅ `config/indicators.csv` — **64 indicators, 3 source systems, 12 categories**
- ✅ `scripts/download_worldbank.R` — 2 batched calls → 2,994 rows
- ✅ `scripts/download_imf.R` — 1 SDMX call → 336 rows, through 2031
- ✅ `scripts/download_vdem.R` — 34MB fetch → 1,673 rows, **1789–2025**
- ✅ `scripts/merge_sources.R` — 3 shapes → one long table, 4,355 rows
- ✅ `scripts/validate.R` — 6 checks, 5 PASS / 1 WARN → HTML report
- ✅ `data_processed/indicators.parquet` + `indicator_metadata.parquet`
- ✅ `scripts/run_all.R` — end-to-end verified from a clean tree

**Verified output:** India GDP 1960 $0.037T → 1991 $0.27T → 2024 $3.76T. Forecast boundary lands
exactly at 2025 actual / 2026 projected. Gini returns its expected 8 points. The single WARN is
literacy + poverty + Gini tripping the <50%-density check — survey cadence, working as designed.

⚠️ `clean_worldbank.R` from the original folder sketch was **never created** — cleaning is 6 lines
inside `merge_sources.R`. A separate file for `as.integer()` and a `left_join` would have been a file
to maintain, not a module.

### Phase 2 — Analytical data model ⏭️ SKIPPED (deliberately)
Derived metrics (CAGR, decade averages, indexed-to-1991) were speculative before knowing which charts
needed them. Q1/Q2 index inline; Q4 rolls its own trailing mean. Revisit when a chart actually demands
a cached derived layer.

### Phase 3 — Shiny app ✅ first cut shipped
- ✅ `app.R` — KPI row + 6 question-led charts, `bslib` layout, one shared year-range control
- ✅ `R/theme.R` — validated palette tokens + shared plotly chrome
- ✅ `R/charts.R` — 6 chart builders, one analytical question each
- ✅ `docs/CHART_RATIONALE.md` — the questions, forms, and traps avoided
- ⬜ Modules (`R/mod_*.R`) — deferred until the app needs more than one page
- ⬜ Dark mode, table view, texture channel — see CHART_RATIONALE "Known gaps"

### Phases 4–10 ⬜ planned
Visualizations → advanced analytics → comparative (BRICS/G20) → storytelling → deploy/CI → docs & tests.

---

## 3. Key Decisions Made

| Concern | User story | Decision | Rationale | Pending concerns |
|---|---|---|---|---|
| ~~R not installed locally~~ | Dev can run pipeline | **Resolved** — R 4.6.1 installed mid-session via `brew install r` | Formula not cask: the cask needs an admin password and would hang a background job | None. Every script was executed, not written blind. Three import bugs were caught before first user run |
| "EcoPolitical" scope | User sees political context | Econ + WGI governance | Same API, no new source, delivers the title | WGI starts 1996 — 36-year gap vs GDP's 1960 |
| Country scope | User views India trends | `IND` only | Your call; keeps parquet tiny | Contradicts your own Step 7 (India vs BRICS). Re-pull = 1 config edit, cheap |
| WGI codes 404 on default API | Governance charts render | Add `wb_source` column to config | `VA.EST` returns **empty**; real code is `GOV_WGI_VA.EST` + `&source=3` | Download loop must branch on `wb_source` |
| CO2 indicator | Environment tab | `EN.GHG.CO2.PC.CE.AR5` | `EN.ATM.CO2E.PC` returns **0 rows** — WB deprecated it | New code is AR5 basis, excludes LULUCF — label it |
| Ease of Doing Business | Governance tab | **Dropped** | `IC.BUS.EASE.XQ` returns 0 rows — WB discontinued the index in 2021 | None |
| Storage format | Fast app load | Parquet via `arrow` | Preserves types, ~50KB for this dataset | `arrow` install on macOS occasionally needs a source build |
| Config vs metadata table | Shiny populates dropdowns | Config is hand-authored, metadata is **generated** | Coverage/last-updated are facts from the API, not opinions — never hand-maintain | None |
| Sparse indicators | Charts don't look broken | Coverage table below sets per-indicator expectations | Gini has 8 points over 45 years — that's the real data, not an ETL bug | Validation must not flag these as failures |
| WB debt gap + no forecasts | User sees debt to today | IMF WEO into Phase 1 | WB dies at 2018; IMF runs 1991→**2031** with forecasts | IMF & WB series overlap — must be labelled, never merged (§3d) |
| Governance floor at 1996 | "EcoPolitical" over *the years* | V-Dem into Phase 1 | 26 WGI points is too thin for the project's core claim; V-Dem goes back to 1789 | See size constraint below |
| **V-Dem is 1.05 GB decompressed** | App loads fast | One-time extract script, filtered parquet only | 34MB download → 1.05GB in memory, 3,868 variables. Loading this in `app.R` would be absurd | `download_vdem.R` must filter to 8 indices + country list, write parquet, and **never** be called at app runtime. Raw file gitignored |
| IMF key order | Fiscal charts populate | `COUNTRY.INDICATOR.FREQUENCY` | `A.IND.GGXWDG_NGDP` → 200 OK, **0 series**. `IND.GGXWDG_NGDP.A` → 41 obs | Same silent-empty class as the WB trap — assert series count |
| IMF returns XML | Parser works | `xml2` not `jsonlite` | `Accept: application/vnd.sdmx.data+json` is **ignored** — SDMX ships XML regardless | Adds `xml2` dep; parse `<Obs TIME_PERIOD OBS_VALUE>` |

**Counterfactual on India-only:** this is wrong if you decide to demo comparative analysis before Phase 7. Cost of being wrong is one line in `download_worldbank.R` and a ~30s re-fetch — accepted.

---

## 3b. Source Ladder (all endpoints hit live, 2026-07-31)

Tiered by what each source is *the only* provider of. Nothing is added for completeness — a source
earns a slot only by filling a gap the tier above it cannot.

| Tier | Source | Fills | Auth | Verified result |
|---|---|---|---|---|
| **1 — backbone** | World Bank `source=2` | 43 indicators, 1960–2025 | none | ✅ 2,838 rows, **one call**, 34KB, 0.43s |
| **1 — backbone** | World Bank `source=3` (WGI) | 6 governance, 1996–2024 | none | ✅ 156 rows, **one call**, 2KB, 0.29s |
| **2 — gap fill** | IMF WEO (`api.imf.org` SDMX 2.1) | Govt debt **2019–2031** (WB dies at 2018) + forecasts | none | ✅ 41 obs 1991–2031 |
| **2 — gap fill** | V-Dem (`vdemdata` GitHub) | Governance **pre-1996**, back to 1789 | none | ✅ HTTP 200, 33.9MB `.RData` |
| **3 — cross-check** | Our World in Data grapher CSV | CO₂ / renewables second opinion | none | ✅ 200, but `?country=` **ignored** — filter client-side |
| **4 — deferred** | RBI, MOSPI | Repo rate, monthly CPI, national accounts | none | ❌ No API. Manual download + parser |
| **4 — deferred** | data.gov.in | State-level detail | **key** | ⚠️ `400 Authorization field missing` — confirmed key-gated |
| **❌ rejected** | IMF legacy `dataservices.imf.org` | — | — | ❌ **Connection refused.** Retired. Any tutorial using it is dead |
| **❌ rejected** | WID (wid.world) | Income/wealth inequality | — | ❌ Both documented endpoints `404`. Revisit only if Gini becomes central |
| **❌ rejected** | ILOSTAT SDMX | Unemployment back-history | none | ❌ Dataflow ID guesses `404`. WB already covers 1991+ — not worth the dig |

**Decision (revised): Phase 1 ships Tier 1 + Tier 2.** 64 indicators from 3 systems. Tier 3–4 stay out
until the backbone is proven — each adds a failure mode (HTML scraping, an expirable key) for marginal
indicators.

### 3c. Multi-country parity — verified

Both Tier-1 and Tier-2 sources were re-tested across the BRICS/G20 peer set. **India is not the weak
link — it has the best coverage of the group.**

World Bank batch, `GDP + CPI`, 132 year-slots per country:

| IND | ZAF | USA | IDN | BRA | CHN | RUS |
|---|---|---|---|---|---|---|
| **132/132** | 132/132 | 131/132 | 125/132 | 111/132 | 105/132 | 71/132 |

IMF WEO `GGXWDG_NGDP` first year: **IND 1991**, GBR/JPN 1990, DEU 1991, CHN 1995, RUS 1997, BRA/IDN/ZAF 2000, **USA 2001**. All run to 2031.

V-Dem: India, China, Brazil, Russia, South Africa, Indonesia, USA, Pakistan, Bangladesh, Nigeria,
Germany, Japan all present; 378 country codes total.

**So the A7 comparison node is unblocked at the source level.** Widening from `IND` to a peer list is a
single config/argument change on all three systems — WB and IMF both accept multi-country in one call
(`IND;CHN;BRA` and `IND+CHN+BRA` respectively), V-Dem is a local filter.

### 3d. Overlapping indicators — deliberate, must be labelled

IMF WEO duplicates four WB series on purpose (`NGDP_RPCH`≈GDP growth, `PCPIPCH`≈CPI,
`NGDPDPC`≈GDP/capita, `BCA_NGDPD`≈current account). Keep both: **WB is history, IMF is history +
forecast to 2031**. They will not match exactly — different vintages and methodologies.

⚠️ Charts must never sum or average across the two. Any "GDP growth" dropdown shows them as two
distinct labelled series (`... (IMF)` suffix is already in the config), and forecast years need visual
separation from actuals (dashed line past the last actual year).

**Decision: keep both (option A).** Both series ship, both are labelled, forecast years render dashed.

`is_forecast` is derived in `merge_sources.R` as `year > max(year of any WB actual)` — not hardcoded.

**Deliberately deferred:** own forecasting models, and any vintage-aware backtest against IMF
projections. Phase 1 does keep the `vintage` column (`COUNTRY_UPDATE_DATE`, e.g. `9/26/2025`) because
it arrives free in the SDMX response and is unrecoverable later — one column, no logic. Frozen
snapshots (`WEO_2025_OCT_VINTAGE`, …) exist if that work is ever picked up. Not building toward it now.

---

## 4. Current Target Implementation Flow

**The throughput finding that rewrote this section:** the World Bank `sources/{id}/series/A;B;C/data`
endpoint accepts **semicolon-delimited indicator lists**. The naive per-indicator loop is 49 requests;
batching by `wb_source` is **2 requests**.

```
  naive loop      49 requests · ~20s · retry/backoff/rate-limit logic required
  batched         2  requests · 0.72s · 36KB gzipped · none of that logic needed
```

Consequence: **no rate limiter, no parallel fetch pool, no request queue, no exponential backoff
ladder.** At two requests, a plain `req_retry(max_tries = 3)` is the entire resilience story. Building
a throttler for two calls would be pure ceremony.

```
config/indicators.csv  (49 rows: category, indicator, code, wb_source, unit)
        │
        v
┌──────────────────────────────────────────────────────────────────┐
│ scripts/download_worldbank.R                                      │
│   read_csv(config) |> split(wb_source)      -> 2 groups (43 | 6)  │
│                                                                    │
│   for each group:                                                  │
│     codes <- paste(code, collapse = ";")                           │
│     GET api.worldbank.org/v2/sources/{wb_source}                   │
│           /country/IND/series/{codes}/data                         │
│           ?format=json&per_page=20000                              │
│       + Accept-Encoding: gzip        (3.6MB -> 211KB on big pulls) │
│       + req_retry(max_tries = 3)                                   │
│     ├── 200 + rows      ──> flatten variable[] -> code|year|value  │
│     ├── 200 + 0 series  ──> HARD ERROR, do not proceed  [the trap] │
│     └── !=200 after 3   ──> abort with the failing URL             │
│   write_json ──> data_raw/source_{id}.json     (2 files, audit)    │
└──────────────────────────────────────────────────────────────────┘
        │
        v
┌──────────────────────────────────────────────────────────────────┐
│ scripts/clean_worldbank.R                                         │
│   bind_rows all ──> long tibble                                   │
│     year  -> integer   value -> double   code -> character        │
│   left_join(config) ──> attach category, indicator, unit          │
│   arrange(code, year) ; drop all-NA indicator groups              │
└──────────────────────────────────────────────────────────────────┘
        │
        v
┌──────────────────────────────────────────────────────────────────┐
│ scripts/validate.R          (6 checks, none fatal — all reported) │
│   ├── duplicate (code, year) pairs          -> must be 0          │
│   ├── year outside 1960..current            -> must be 0          │
│   ├── non-numeric / Inf / NaN in value      -> must be 0          │
│   ├── indicator with 0 non-NA rows          -> warn (dead code)   │
│   ├── coverage vs expected table (§5)       -> warn on drop       │
│   └── interior year gaps per indicator      -> report, not fail   │
│   rmarkdown::render ──> docs/validation_report.html               │
└──────────────────────────────────────────────────────────────────┘
        │
        v
   data_processed/
   ├── world_bank.parquet        (long: code, year, value, category, indicator, unit)
   └── indicator_metadata.parquet (code, indicator, category, unit, source,
                                    first_year, last_year, n_obs, pct_coverage)
        │
        v
   app.R  ──> reads metadata ──> populates every dropdown/filter
```

**Why long format, not wide:** 49 indicators × 66 years = ~2,500 rows. Wide would be 49 sparse columns with different year ranges — every chart would need its own `drop_na`. Long + `filter(code == input$code)` is one code path for every chart. Pivot wide only in the correlation module, cached.

---

## 5. Verified Data Coverage (measured against live API, 2026-07-31)

Sets validation expectations. An indicator falling below these is a regression, not a surprise.

| Coverage band | Count | Indicators |
|---|---|---|
| **Full (1960–2025, 65+ pts)** | 19 | GDP family, CPI, trade block, sector value-added, population block, reserves, exchange rate, military spend |
| **Modern (1990+, 30–56 pts)** | 17 | Unemployment, FDI, PPP GDP, female labor, electricity, internet, mobile, renewables, forest, CO2, secondary/tertiary enrollment |
| **Partial (20–29 pts)** | 9 | Central govt debt (1990–2018, **ends 2018**), education spend, health spend, all 6 governance (1996–2024) |
| **Sparse (≤14 pts)** | 4 | Adult literacy (14), Gini (8), poverty headcount (8) |

⚠️ **Three land mines for the UI:**
- `GC.DOD.TOTL.GD.ZS` stops at **2018** — a "latest value" tile will look broken. Show as-of year.
- `SI.POV.GINI` / `SI.POV.DDAY` have **8 points across 45 years** — line charts will look like scatter. Use points + connecting line, never smooth.
- Governance series start **1996** — any econ-vs-governance correlation is limited to 1996+, n≈29.

---

## 6. Timeline of Work

```
Phase                          Effort              LOC      Decision load
─────────────────────────────────────────────────────────────────────────
0  Repo split + config       ████                 ~60      ███  (source/code archaeology)
1  ETL: download+clean+valid ▓▓▓▓▓▓▓▓            ~250      ▓▓▓▓ (retry, sparse-data policy)
2  Analytical model          ▓▓▓▓                ~120      ▓▓▓  (index base year, CAGR windows)
3  Shiny architecture        ▓▓▓▓▓▓              ~200      ▓▓▓▓▓ (module boundaries)
4  Visualizations            ▓▓▓▓▓▓▓             ~300      ▓▓▓
5  Advanced analytics        ▓▓▓▓▓               ~180      ▓▓▓▓ (forecast method choice)
6  Comparative (BRICS/G20)   ▓▓▓▓                ~150      ▓▓   (re-pull, mostly mechanical)
7  Storytelling / insights   ▓▓▓▓▓               ~200      ▓▓▓▓▓ (what counts as an insight)
8  Deploy + CI + refresh     ▓▓▓                 ~80       ▓▓▓
9  Docs + tests              ▓▓▓▓                ~150      ▓▓
─────────────────────────────────────────────────────────────────────────
next ▶ Phase 1 scripts — blocked on nothing, ready to write
```

---

## 7. User Stories

**Implemented ✅**
- `US-000` Repo hosts multiple independent projects without collision

**Next (Phase 1)**
- `US-001` Analyst adds an indicator by appending one CSV row — no code change
- `US-002` Pipeline fetches all 49 indicators unattended, survives a single endpoint failing
- `US-003` Pipeline emits a validation report naming every gap and dead code
- `US-004` App loads a typed, compressed dataset in one `read_parquet`
- `US-005` Dropdowns build themselves from generated metadata

**Later**
- `US-006` User sees India indexed to 1991 liberalization baseline
- `US-007` User overlays democracy/governance scores on economic series
- `US-008` User compares India to BRICS peers
- `US-009` User downloads a rendered report of the current view
- `US-010` User sees IMF projections past the last actual year, rendered dashed

**Deferred indefinitely** (revisit only if the dashboard demands it)
- `US-011` Own forecasting models benchmarked against IMF WEO vintages

---

## 8. Open Questions

1. **Forecasting method (Phase 6)** — `forecast::auto.arima` vs `fable`? Defer until data model lands. Whatever it is, it gets scored against IMF WEO per §3e, so the backtest harness matters more than the model choice.
2. **Policy-event timeline** — you picked econ+governance, *not* the hand-curated event overlay (1991/2016/GST/COVID). Confirm that stays out, or it becomes a `config/events.csv`.
3. **RBI / MOSPI / data.gov.in** — all in your source plan, none in Phase 1. These are scrape-or-download, not API. Propose deferring to Phase 6+ once WB backbone is proven.
4. **Deploy target** — shinyapps.io free tier vs Posit Connect Cloud vs Docker? Affects Phase 9 only.
