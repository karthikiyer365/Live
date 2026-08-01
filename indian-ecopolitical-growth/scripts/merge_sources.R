# Unify 3 source shapes -> data_processed/{indicators,indicator_metadata}.parquet
#
# Long format on purpose: 64 indicators with different year ranges would be 64
# sparse columns if pivoted wide, and every chart would need its own drop_na.
# Long + filter(code == input$code) is one code path for every chart.

source("scripts/utils.R")

suppressPackageStartupMessages({
  library(nanoparquet)
  library(tidyr)
  library(purrr)
})

main <- function() {
  ensure_dirs()
  cfg <- read_indicator_config()

  parts <- c("worldbank.rds", "imf.rds", "vdem.rds")
  missing <- parts[!file.exists(path_raw(parts))]
  if (length(missing) > 0) {
    stop("run the download scripts first — missing: ", paste(missing, collapse = ", "),
         call. = FALSE)
  }

  raw <- map(parts, ~ readRDS(path_raw(.x))) |> bind_rows()

  tidy <- raw |>
    filter(!is.na(value)) |>
    left_join(cfg, by = c("code", "source_system")) |>
    arrange(code, year)

  orphans <- tidy |> filter(is.na(indicator)) |> distinct(code, source_system)
  if (nrow(orphans) > 0) {
    stop("codes present in data but absent from config: ",
         paste(orphans$code, collapse = ", "), call. = FALSE)
  }

  # Forecast flag is derived, not hardcoded: anything past the last year for
  # which we hold a real WB observation is a projection.
  last_actual <- tidy |> filter(source_system == "WB") |> pull(year) |> max()
  tidy <- tidy |> mutate(is_forecast = year > last_actual)
  log_step("last actual year = %d; %d forecast rows flagged",
           last_actual, sum(tidy$is_forecast))

  write_parquet(tidy, path_processed("indicators.parquet"))

  # Metadata is DERIVED, never hand-written — the only honest record of what
  # the APIs actually returned today. app.R builds every dropdown from this.
  meta <- tidy |>
    group_by(code, indicator, category, unit, source_system) |>
    summarise(
      first_year = min(year),
      last_year  = max(year),
      n_obs      = n(),
      pct_coverage = round(100 * n() / (max(year) - min(year) + 1), 1),
      vintage    = first(vintage),
      .groups    = "drop"
    ) |>
    arrange(category, indicator)

  write_parquet(meta, path_processed("indicator_metadata.parquet"))

  log_step("wrote %d rows across %d indicators", nrow(tidy), nrow(meta))
  invisible(list(data = tidy, meta = meta))
}

if (sys.nframe() == 0) main()
