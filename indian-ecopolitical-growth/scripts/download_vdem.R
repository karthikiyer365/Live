# V-Dem -> data_raw/vdem.rds
#
# SIZE WARNING: the download is 34MB but expands to ~1.05 GB in memory with
# 3,868 variables. This script exists so that happens EXACTLY ONCE, offline.
# It must never be called from app.R.
#
# We keep the 8 indices in config and drop everything else before saving.

source("scripts/utils.R")

suppressPackageStartupMessages({
  library(purrr)
  library(tidyr)
})

VDEM_URL <- "https://raw.githubusercontent.com/vdeminstitute/vdemdata/master/data/vdem.RData"
COUNTRY  <- "India"   # V-Dem filters locally on country_name

fetch_vdem <- function(codes) {
  local_copy <- path_raw("vdem.RData")

  if (!file.exists(local_copy)) {
    log_step("V-Dem: downloading 34MB (expands to ~1GB — one time only)")
    download.file(VDEM_URL, local_copy, mode = "wb", quiet = TRUE)
  } else {
    log_step("V-Dem: reusing cached %s", local_copy)
  }

  # load() drops its object into an env; grab it without guessing the name
  env <- new.env()
  obj <- load(local_copy, envir = env)
  vdem <- env[[obj[1]]]
  log_step("V-Dem: loaded %d rows x %d cols", nrow(vdem), ncol(vdem))

  missing_cols <- setdiff(codes, names(vdem))
  if (length(missing_cols) > 0) {
    stop("V-Dem is missing configured columns: ", paste(missing_cols, collapse = ", "),
         call. = FALSE)
  }

  out <- vdem |>
    filter(country_name %in% COUNTRY) |>
    select(country = country_text_id, year, all_of(codes)) |>
    pivot_longer(all_of(codes), names_to = "code", values_to = "value") |>
    filter(!is.na(value)) |>
    mutate(source_system = "VDEM", vintage = NA_character_)

  assert_series_complete(unique(out$code), codes, "V-Dem")

  # free the 1GB before the next script runs
  rm(vdem, env); gc(verbose = FALSE)

  log_step("V-Dem: %d rows, %d-%d", nrow(out), min(out$year), max(out$year))
  out
}

main <- function() {
  ensure_dirs()
  cfg <- read_indicator_config() |> filter(source_system == "VDEM")

  vd <- fetch_vdem(cfg$code)

  saveRDS(vd, path_raw("vdem.rds"))
  log_step("wrote %s (%d rows)", path_raw("vdem.rds"), nrow(vd))
  invisible(vd)
}

if (sys.nframe() == 0) main()
