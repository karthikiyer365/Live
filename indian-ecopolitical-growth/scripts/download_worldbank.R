# World Bank -> data_raw/worldbank.rds
#
# The whole WB pull is 2 requests, not 49. The sources/{id}/series/A;B;C/data
# endpoint takes a semicolon-delimited code list; we batch by source_param.
# Measured: 2838 + 156 rows, 36KB gzipped, 0.72s total.
#
# ponytail: no rate limiter, no pool, no queue, no backoff ladder. Two requests.

source("scripts/utils.R")

suppressPackageStartupMessages({
  library(httr2)
  library(purrr)
})

WB_BASE  <- "https://api.worldbank.org/v2"
COUNTRY  <- "IND"   # widen here for Phase 7 comparison; WB accepts "IND;CHN;BRA"

fetch_wb_batch <- function(source_param, codes) {
  url <- sprintf("%s/sources/%s/country/%s/series/%s/data",
                 WB_BASE, source_param, COUNTRY, paste(codes, collapse = ";"))

  log_step("WB source=%s: requesting %d series", source_param, length(codes))

  resp <- request(url) |>
    req_url_query(format = "json", per_page = 20000) |>
    req_headers(`Accept-Encoding` = "gzip") |>
    req_retry(max_tries = 3) |>
    req_perform()

  writeLines(resp_body_string(resp), path_raw(sprintf("worldbank_source_%s.json", source_param)))

  rows <- resp_body_json(resp)$source$data
  if (length(rows) == 0) {
    stop(sprintf("WB source=%s returned 0 rows (HTTP %d)", source_param, resp_status(resp)),
         call. = FALSE)
  }
  # ponytail: a code requested against the WRONG source_param fails differently —
  # WB answers with XML and httr2 raises 'Unexpected content type "text/xml"'.
  # Cryptic, but loud and unmissable, so no extra handling. If you see it, you
  # put a source=3 code on source=2 (or vice versa) in indicators.csv.

  # Response nests dimensions in a `variable` array — there is no top-level
  # `date` or `indicator.id`. Pivot on `concept`, and note Time is "YR2025".
  pick <- function(vars, concept) {
    hit <- keep(vars, ~ .x$concept == concept)
    if (length(hit) == 0) NA_character_ else hit[[1]]$id
  }

  out <- tibble(
    code    = map_chr(rows, ~ pick(.x$variable, "Series")),
    country = map_chr(rows, ~ pick(.x$variable, "Country")),
    year    = as.integer(sub("^YR", "", map_chr(rows, ~ pick(.x$variable, "Time")))),
    value   = map_dbl(rows, ~ if (is.null(.x$value)) NA_real_ else as.numeric(.x$value))
  )

  assert_series_complete(unique(out$code), codes, sprintf("WB source=%s", source_param))
  stopifnot("year failed to parse — check the YR prefix strip" = !all(is.na(out$year)))

  log_step("WB source=%s: %d rows, %d non-NA", source_param, nrow(out), sum(!is.na(out$value)))
  out
}

main <- function() {
  ensure_dirs()
  cfg <- read_indicator_config() |> filter(source_system == "WB")

  wb <- cfg |>
    group_by(source_param) |>
    group_split() |>
    map(~ fetch_wb_batch(.x$source_param[1], .x$code)) |>
    bind_rows() |>
    mutate(source_system = "WB", vintage = NA_character_)

  saveRDS(wb, path_raw("worldbank.rds"))
  log_step("wrote %s (%d rows)", path_raw("worldbank.rds"), nrow(wb))
  invisible(wb)
}

if (sys.nframe() == 0) main()
