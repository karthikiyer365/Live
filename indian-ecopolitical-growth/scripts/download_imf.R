# IMF WEO -> data_raw/imf.rds
#
# Two things that cost time if you don't know them:
#   1. Key order is COUNTRY.INDICATOR.FREQUENCY. Any other order returns
#      HTTP 200 with ZERO series — silent failure, not an error.
#   2. `Accept: application/vnd.sdmx.data+json` is IGNORED. SDMX ships XML
#      regardless, so this parses with xml2, not jsonlite.
#
# The legacy dataservices.imf.org endpoint is DEAD (connection refused).
# Any tutorial using it will not work.

source("scripts/utils.R")

suppressPackageStartupMessages({
  library(httr2)
  library(xml2)
  library(purrr)
})

IMF_BASE <- "https://api.imf.org/external/sdmx/2.1/data"
COUNTRY  <- "IND"   # IMF joins with "+", not ";" — e.g. "IND+CHN+BRA"

fetch_imf_weo <- function(codes) {
  key <- sprintf("%s.%s.A", COUNTRY, paste(codes, collapse = "+"))
  url <- file.path(IMF_BASE, "WEO", key)

  log_step("IMF WEO: requesting %d series", length(codes))

  resp <- request(url) |>
    req_url_query(startPeriod = 1960) |>
    req_retry(max_tries = 3) |>
    req_perform()

  writeLines(resp_body_string(resp), path_raw("imf_weo.xml"))

  doc    <- read_xml(resp_body_string(resp))
  series <- xml_find_all(doc, "//*[local-name()='Series']")

  if (length(series) == 0) {
    stop("IMF returned 0 series. Key order must be COUNTRY.INDICATOR.FREQUENCY — ",
         "a wrong order still returns HTTP 200.", call. = FALSE)
  }

  out <- map(series, function(s) {
    obs <- xml_find_all(s, "./*[local-name()='Obs']")
    if (length(obs) == 0) return(NULL)
    tibble(
      code    = xml_attr(s, "INDICATOR"),
      country = xml_attr(s, "COUNTRY"),
      year    = as.integer(xml_attr(obs, "TIME_PERIOD")),
      value   = as.numeric(xml_attr(obs, "OBS_VALUE")),
      # arrives free in the response; unrecoverable later, so keep it
      vintage = xml_attr(s, "COUNTRY_UPDATE_DATE")
    )
  }) |> compact() |> bind_rows()

  assert_series_complete(unique(out$code), codes, "IMF WEO")

  log_step("IMF WEO: %d rows, %d non-NA, through %d",
           nrow(out), sum(!is.na(out$value)), max(out$year, na.rm = TRUE))
  out
}

main <- function() {
  ensure_dirs()
  cfg <- read_indicator_config() |> filter(source_system == "IMF")

  imf <- fetch_imf_weo(cfg$code) |> mutate(source_system = "IMF")

  saveRDS(imf, path_raw("imf.rds"))
  log_step("wrote %s (%d rows)", path_raw("imf.rds"), nrow(imf))
  invisible(imf)
}

if (sys.nframe() == 0) main()
