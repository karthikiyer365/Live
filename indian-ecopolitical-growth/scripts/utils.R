# Shared helpers. Sourced by every script — the config is read in exactly one place.

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
})

# ponytail: paths resolved from the working directory, not __file__ gymnastics.
# All scripts are meant to be run from the project root via run_all.R.
path_config    <- function(...) file.path("config", ...)
path_raw       <- function(...) file.path("data_raw", ...)
path_processed <- function(...) file.path("data_processed", ...)
path_docs      <- function(...) file.path("docs", ...)

#' The single source of truth. Never re-read indicators.csv anywhere else.
read_indicator_config <- function() {
  cfg <- read_csv(
    path_config("indicators.csv"),
    col_types = cols(
      category      = col_character(),
      indicator     = col_character(),
      code          = col_character(),
      source_system = col_character(),
      source_param  = col_character(),
      unit          = col_character()
    )
  )

  stopifnot(
    "config has no rows"            = nrow(cfg) > 0,
    "duplicate indicator codes"     = !any(duplicated(cfg$code)),
    "unknown source_system present" = all(cfg$source_system %in% c("WB", "IMF", "VDEM"))
  )
  cfg
}

#' Every source in this project returns HTTP 200 with an empty payload when the
#' request is subtly wrong (WB: bad source id; IMF: wrong key order). Silence is
#' the dominant failure mode, so a short fetch is a hard error, never a warning.
assert_series_complete <- function(got_codes, want_codes, source_label) {
  missing <- setdiff(want_codes, got_codes)
  if (length(missing) > 0) {
    stop(sprintf(
      "%s returned %d/%d series. Missing: %s\nHTTP 200 with missing series means the request was wrong, not that the data is absent.",
      source_label, length(intersect(got_codes, want_codes)), length(want_codes),
      paste(missing, collapse = ", ")
    ), call. = FALSE)
  }
  invisible(TRUE)
}

ensure_dirs <- function() {
  for (d in c("data_raw", "data_processed", "docs")) {
    if (!dir.exists(d)) dir.create(d, recursive = TRUE)
  }
}

log_step <- function(...) cat(sprintf("[%s] %s\n", format(Sys.time(), "%H:%M:%S"), sprintf(...)))
