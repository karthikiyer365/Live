# 6 checks over the processed dataset -> console + docs/validation_report.html
#
# Design rule that matters: sparse != broken. Gini has 8 observations across 45
# years, literacy 14, poverty 8. That is survey cadence, not an ETL bug. A naive
# "no missing years" check FAILS 4 of 64 indicators on a perfectly healthy run,
# so gap checks WARN and never fail the build.

source("scripts/utils.R")

suppressPackageStartupMessages({
  library(arrow)
  library(purrr)
})

checks <- list(

  duplicate_rows = function(d, m) {
    bad <- d |> count(code, year, country) |> filter(n > 1)
    list(fail = nrow(bad) > 0, n = nrow(bad),
         msg = "duplicate (code, year, country) rows")
  },

  year_range = function(d, m) {
    bad <- d |> filter(year < 1780 | year > as.integer(format(Sys.Date(), "%Y")) + 10)
    list(fail = nrow(bad) > 0, n = nrow(bad),
         msg = "years outside 1780..now+10 (V-Dem legitimately starts 1789)")
  },

  numeric_sanity = function(d, m) {
    bad <- d |> filter(!is.finite(value))
    list(fail = nrow(bad) > 0, n = nrow(bad),
         msg = "non-finite values (NaN/Inf) survived cleaning")
  },

  dead_indicators = function(d, m) {
    bad <- m |> filter(n_obs == 0)
    list(fail = FALSE, n = nrow(bad), warn = TRUE,
         detail = bad$code,
         msg = "indicators with zero observations (dead code at source)")
  },

  config_completeness = function(d, m) {
    cfg <- read_indicator_config()
    bad <- setdiff(cfg$code, m$code)
    list(fail = length(bad) > 0, n = length(bad), detail = bad,
         msg = "configured indicators that produced no data")
  },

  interior_gaps = function(d, m) {
    gappy <- d |>
      group_by(code) |>
      summarise(span = max(year) - min(year) + 1, obs = n(), .groups = "drop") |>
      filter(obs < span * 0.5)
    list(fail = FALSE, n = nrow(gappy), warn = TRUE,
         detail = gappy$code,
         msg = "indicators covering <50% of their own span (report only — survey cadence)")
  }
)

main <- function() {
  ensure_dirs()
  d <- read_parquet(path_processed("indicators.parquet"))
  m <- read_parquet(path_processed("indicator_metadata.parquet"))

  results <- imap(checks, function(fn, nm) {
    r <- fn(d, m)
    status <- if (isTRUE(r$fail)) "FAIL" else if (isTRUE(r$warn) && r$n > 0) "WARN" else "PASS"
    cat(sprintf("  [%-4s] %-22s %3d  %s\n", status, nm, r$n, r$msg))
    if (!is.null(r$detail) && length(r$detail) > 0) {
      cat(sprintf("         -> %s\n", paste(r$detail, collapse = ", ")))
    }
    modifyList(r, list(name = nm, status = status))
  })

  cat(sprintf("\n  %d indicators | %d rows | %d-%d\n",
              nrow(m), nrow(d), min(d$year), max(d$year)))

  write_report(results, d, m)

  if (any(map_chr(results, "status") == "FAIL")) {
    stop("validation failed — see output above", call. = FALSE)
  }
  invisible(results)
}

write_report <- function(results, d, m) {
  rows <- paste(map_chr(results, function(r) sprintf(
    "<tr class='%s'><td>%s</td><td>%s</td><td>%d</td><td>%s</td></tr>",
    tolower(r$status), r$status, r$name, r$n, r$msg)), collapse = "\n")

  cov <- paste(pmap_chr(m, function(...) {
    x <- list(...)
    sprintf("<tr><td>%s</td><td>%s</td><td>%s</td><td>%d-%d</td><td>%d</td><td>%.1f%%</td></tr>",
            x$category, x$indicator, x$source_system, x$first_year, x$last_year,
            x$n_obs, x$pct_coverage)
  }), collapse = "\n")

  html <- sprintf("<!doctype html><meta charset='utf-8'>
<title>Validation report</title>
<style>
 body{font-family:system-ui,sans-serif;margin:2rem;max-width:1000px}
 table{border-collapse:collapse;width:100%%;margin:1rem 0}
 th,td{border:1px solid #ddd;padding:.4rem .6rem;text-align:left;font-size:.9rem}
 th{background:#f4f4f4}
 .pass td:first-child{color:#137333;font-weight:600}
 .warn td:first-child{color:#b06000;font-weight:600}
 .fail td:first-child{color:#c5221f;font-weight:600}
</style>
<h1>Validation report</h1>
<p>Generated %s — %d indicators, %d rows, %d–%d.</p>
<h2>Checks</h2>
<table><tr><th>Status</th><th>Check</th><th>Count</th><th>Meaning</th></tr>%s</table>
<h2>Coverage by indicator</h2>
<table><tr><th>Category</th><th>Indicator</th><th>Source</th><th>Years</th><th>Obs</th><th>Density</th></tr>%s</table>",
    format(Sys.time(), "%%Y-%%m-%%d %%H:%%M"), nrow(m), nrow(d),
    min(d$year), max(d$year), rows, cov)

  writeLines(html, path_docs("validation_report.html"))
  log_step("wrote %s", path_docs("validation_report.html"))
}

if (sys.nframe() == 0) main()
