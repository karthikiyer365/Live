# Understanding Indian EcoPolitical Growth Over the Years
#
# Six charts, one analytical question each. Reads the Phase 1 parquet — the ETL
# is never invoked at runtime. Rationale for every chart choice, and the traps
# each one avoids, is in docs/CHART_RATIONALE.md.

suppressPackageStartupMessages({
  library(shiny)
  library(bslib)
  library(arrow)
  library(dplyr)
  library(plotly)
})

source("R/theme.R")
source("R/charts.R")

DATA <- read_parquet("data_processed/indicators.parquet")
META <- read_parquet("data_processed/indicator_metadata.parquet")

QUESTIONS <- list(
  list(id = "q1", q = "Does headline GDP flatter what actually reached each person?",
       note = paste("Total GDP and GDP per capita differ by three orders of magnitude, so they are",
                    "indexed to a common base on one axis. Two y-scales would invent a relationship",
                    "that isn't in the data."),
       fn = function(d) chart_growth_inflection(d)),

  list(id = "q2", q = "Do prosperity and democratic depth move together, or diverge?",
       note = paste("The core eco-political question. Small multiples, not one shared axis: V-Dem is a",
                    "bounded 0–1 index while GDP per capita grew roughly seventyfold, so forcing them",
                    "onto one scale would flatten democracy into a straight line and hide the answer."),
       fn = function(d) chart_democracy_vs_prosperity(d)),

  list(id = "q3", q = "Did India skip the manufacturing stage other economies went through?",
       note = paste("Deliberately three lines, not a stacked area: World Bank value-added shares sum to",
                    "about 91%, not 100 (they exclude taxes less subsidies on products). Stacking would",
                    "fake a part-to-whole that does not exist."),
       fn = function(d) chart_structural_transition(d)),

  list(id = "q4", q = "Which years are genuine shocks rather than noise?",
       note = paste("Each year's growth measured against the economy's own trailing 10-year mean, so the",
                    "baseline is India's norm rather than an arbitrary zero. Diverging colour with a",
                    "neutral zero line."),
       fn = function(d) chart_shock_detector(d)),

  list(id = "q5", q = "Did growth actually reach women?",
       note = paste("A connected scatter, not two time series: prosperity on x, female participation on y,",
                    "time as the colour channel. If growth were inclusive the path would climb to the",
                    "right. Watch what it does between 2000 and 2020."),
       fn = function(d) chart_growth_vs_inclusion(d)),

  list(id = "q6", q = "Where is our evidence weakest?",
       note = paste("Measurement bias made visible. Density of observations per category per decade.",
                    "The thinnest rows are inequality and poverty — the questions where the data is",
                    "weakest are the ones people argue about most."),
       fn = function(d) chart_evidence_density(d))
)

ui <- page_fluid(
  theme = bs_theme(version = 5, bg = "#f9f9f7", fg = "#0b0b0b", primary = "#2a78d6",
                   base_font = font_google("Inter", local = FALSE)),
  tags$style(HTML(sprintf("
    .q-card { background:%s; border:1px solid rgba(11,11,11,.10); border-radius:10px;
              padding:18px 20px 8px; margin-bottom:20px; }
    .q-title { font-size:1.02rem; font-weight:600; color:%s; margin:0 0 2px; }
    .q-note  { font-size:.83rem; color:%s; margin:0 0 10px; max-width:75ch; line-height:1.45; }
    .hero    { font-size:2.6rem; font-weight:650; letter-spacing:-.02em; color:%s;
               font-variant-numeric:tabular-nums; line-height:1.1; }
    .hero-l  { font-size:.78rem; color:%s; text-transform:uppercase; letter-spacing:.06em; }
    .hero-s  { font-size:.8rem; color:%s; }
  ", PAL$surface, PAL$ink, PAL$ink_2, PAL$ink, PAL$muted, PAL$ink_2))),

  div(style = "max-width:1080px;margin:0 auto;padding:28px 20px 60px",
      h2("Understanding Indian EcoPolitical Growth", style = "font-weight:650;margin-bottom:2px"),
      p(sprintf("%d indicators · %d–%d · World Bank, IMF WEO, V-Dem",
                nrow(META), min(DATA$year), max(DATA$year)),
        style = sprintf("color:%s;font-size:.86rem;margin-bottom:22px", PAL$muted)),

      # KPI row — headline numbers are stat tiles, not one-bar charts.
      # A flex row, not layout_columns: a single uiOutput is ONE child, so
      # col_widths never splits it and all four tiles stack vertically.
      uiOutput("kpis"),

      div(style = "height:20px"),

      # Single shared control, one row above the charts
      div(style = "margin-bottom:18px",
          sliderInput("yrs", "Year range", min = 1900, max = max(DATA$year),
                      value = c(1960, max(DATA$year)), sep = "", width = "100%")),

      uiOutput("charts"),

      p(HTML(paste("Sources: World Bank Open Data · IMF World Economic Outlook · V-Dem v15.",
                   "Projections past the last actual year are IMF estimates.")),
        style = sprintf("color:%s;font-size:.78rem;margin-top:26px", PAL$muted))
  )
)

server <- function(input, output, session) {

  filtered <- reactive({
    DATA |> filter(year >= input$yrs[1], year <= input$yrs[2])
  })

  latest_of <- function(cd) {
    r <- DATA |> filter(code == cd, !is_forecast) |> filter(year == max(year))
    if (nrow(r) == 0) return(list(v = NA, y = NA))
    list(v = r$value[1], y = r$year[1])
  }

  output$kpis <- renderUI({
    tile <- function(label, value, sub) {
      div(class = "q-card", style = "padding:16px 18px",
          div(class = "hero-l", label),
          div(class = "hero", value),
          div(class = "hero-s", sub))
    }
    gdp <- latest_of("NY.GDP.MKTP.CD"); pc <- latest_of("NY.GDP.PCAP.CD")
    dem <- latest_of("v2x_polyarchy");  gr <- latest_of("NY.GDP.MKTP.KD.ZG")
    div(style = "display:flex;gap:14px;flex-wrap:wrap",
        div(style = "flex:1 1 180px", tile("GDP", sprintf("$%.2fT", gdp$v / 1e12), sprintf("%d", gdp$y))),
        div(style = "flex:1 1 180px", tile("GDP per capita",
              sprintf("$%s", format(round(pc$v), big.mark = ",")), sprintf("%d", pc$y))),
        div(style = "flex:1 1 180px", tile("GDP growth", sprintf("%.1f%%", gr$v), sprintf("%d", gr$y))),
        div(style = "flex:1 1 180px", tile("Democracy index", sprintf("%.2f", dem$v),
              sprintf("V-Dem 0–1 · %d", dem$y))))
  })

  output$charts <- renderUI({
    lapply(QUESTIONS, function(qq) {
      div(class = "q-card",
          p(class = "q-title", qq$q),
          p(class = "q-note", qq$note),
          plotlyOutput(qq$id, height = "340px"))
    })
  })

  # bind each question to its renderer
  lapply(QUESTIONS, function(qq) {
    output[[qq$id]] <- renderPlotly(qq$fn(filtered()))
  })
}

shinyApp(ui, server)
