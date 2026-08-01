# Phase 1 pipeline. Run from the project root:
#   Rscript scripts/run_all.R

stopifnot("run this from the project root (config/ not found)" = dir.exists("config"))

for (step in c("download_worldbank", "download_imf", "download_vdem",
               "merge_sources", "validate")) {
  cat(sprintf("\n=== %s ===\n", step))
  source(file.path("scripts", paste0(step, ".R")))
  main()
}

cat("\nPhase 1 complete.\n")
