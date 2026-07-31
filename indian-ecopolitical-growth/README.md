# Understanding Indian EcoPolitical Growth Over the Years

An R Shiny dashboard tracing India's economic **and governance** trajectory from 1960 to today —
49 World Bank indicators, zero API keys, driven entirely by one CSV config.

> **Status: Phase 1, planning complete, no R code yet.**
> `config/indicators.csv` is real and API-verified. Everything else is specified, not built.

## Where to start

| File | What it is |
|---|---|
| [`BUILD_PLAN.md`](./BUILD_PLAN.md) | The plan — decisions, verified data coverage, 10-phase roadmap |
| [`docs/TOPICAL_MAP.md`](./docs/TOPICAL_MAP.md) | Target topology as ASCII maps; `▓` marks what doesn't exist yet |
| [`config/indicators.csv`](./config/indicators.csv) | 49 indicators, 11 categories — the source of truth |

## Why governance data

Most India dashboards stop at GDP. This one pairs macro series with the World Bank's
**Worldwide Governance Indicators** — rule of law, control of corruption, government
effectiveness, political stability, regulatory quality, voice and accountability — which is the
"political" half of the title.

Catch: WGI lives in a **separate World Bank database**. `RL.EST` returns HTTP 200 with an empty
body. The working call is:

```
https://api.worldbank.org/v2/country/IND/indicator/GOV_WGI_RL.EST?format=json&source=3
```

Hence the `wb_source` column in the config. See `BUILD_PLAN.md` §3.

## Planned structure

```
indian-ecopolitical-growth/
├── config/indicators.csv       ✅ exists — 49 rows
├── scripts/
│   ├── download_worldbank.R    ▓ planned
│   ├── clean_worldbank.R       ▓ planned
│   ├── merge_sources.R         ▓ planned
│   └── validate.R              ▓ planned
├── data_raw/                   ▓ gitignored, created by ETL
├── data_processed/             ▓ world_bank.parquet + indicator_metadata.parquet
├── app.R                       ▓ planned
├── BUILD_PLAN.md               ✅
└── docs/TOPICAL_MAP.md         ✅
```

## Prerequisites (not yet installed on the dev machine)

```bash
brew install --cask r
brew install pandoc          # for the validation report
```

```r
install.packages(c("shiny", "bslib", "httr2", "jsonlite", "dplyr", "tidyr",
                   "readr", "purrr", "arrow", "rmarkdown", "plotly", "DT"))
```

## Data sources

| Source | Role | Key required |
|---|---|---|
| World Bank Open Data | Backbone — all 49 indicators, Phase 1 | No |
| World Bank WGI (`source=3`) | Governance, 1996+ | No |
| Our World in Data | Energy / CO₂ cross-check, Phase 6+ | No |
| IMF, RBI, MOSPI, data.gov.in | India-specific depth, Phase 6+ | Varies |
