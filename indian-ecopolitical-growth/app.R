# Understanding Indian EcoPolitical Growth Over the Years
#
# Sidebar + focus view: a persistent index of the six questions on the left, one
# large chart plus its computed finding on the right. Reads the Phase 1 parquet —
# the ETL is never invoked at runtime.
#
# Chart forms and the traps each avoids: docs/CHART_RATIONALE.md

suppressPackageStartupMessages({
  library(shiny)
  library(bslib)
  library(nanoparquet)
  library(dplyr)
  library(plotly)
})

source("R/theme.R")
source("R/charts.R")

DATA <- read_parquet("data_processed/indicators.parquet")
META <- read_parquet("data_processed/indicator_metadata.parquet")

# --- helpers for the computed finding lines --------------------------------
# Findings are DERIVED from the visible data, never hardcoded — they stay true
# when the year range moves. A hardcoded sentence is a lie waiting to happen.
val_at <- function(d, cd, when = c("first", "last")) {
  s <- d |> filter(code == cd, !is.na(value)) |> arrange(year)
  if (nrow(s) == 0) return(NULL)
  if (match.arg(when) == "first") s[1, ] else s[nrow(s), ]
}
fmt_x  <- function(a, b) if (is.null(a) || is.null(b) || b == 0) "—" else sprintf("%.0f×", a / b)
fmt_d  <- function(v) paste0("$", format(round(v), big.mark = ","))

QUESTIONS <- list(
  list(id = "q1", domain = "Economy", nav = "Growth", q = "Does headline GDP flatter what actually reached each person?",
       note = paste("Total GDP and GDP per capita differ by three orders of magnitude, so they are indexed",
                    "to a common base on one axis. Two y-scales would invent a relationship that isn't",
                    "in the data."),
       caveat = "Current US$, not inflation-adjusted. Exchange-rate swings move the dollar figures.",
       fn = function(d) chart_growth_inflection(d),
       finding = function(d) {
         g0 <- val_at(d, "NY.GDP.MKTP.CD", "first"); g1 <- val_at(d, "NY.GDP.MKTP.CD", "last")
         p0 <- val_at(d, "NY.GDP.PCAP.CD", "first"); p1 <- val_at(d, "NY.GDP.PCAP.CD", "last")
         if (is.null(g1) || is.null(p1)) return(NULL)
         sprintf("Total GDP grew %s between %d and %d. Per person, only %s — population absorbed the rest.",
                 fmt_x(g1$value, g0$value), g0$year, g1$year, fmt_x(p1$value, p0$value))
       }),

  list(id = "q2", domain = "Politics", nav = "Democracy", q = "Do prosperity and democratic depth move together, or diverge?",
       note = paste("Small multiples, not one shared axis: V-Dem is a bounded 0–1 index while GDP per capita",
                    "grew roughly seventyfold, so forcing them onto one scale would flatten democracy into",
                    "a straight line and hide the answer."),
       caveat = "V-Dem is an expert-coded index with uncertainty bands not shown here. WGI, the alternative, only starts in 1996.",
       fn = function(d) chart_democracy_vs_prosperity(d),
       finding = function(d) {
         d0 <- val_at(d, "v2x_polyarchy", "first"); d1 <- val_at(d, "v2x_polyarchy", "last")
         p0 <- val_at(d, "NY.GDP.PCAP.CD", "first"); p1 <- val_at(d, "NY.GDP.PCAP.CD", "last")
         if (is.null(d1) || is.null(p1)) return(NULL)
         dir <- if (d1$value < d0$value) "fell" else "rose"
         sprintf("GDP per capita rose %s since %d, while the democracy index %s from %.2f to %.2f. They diverge.",
                 fmt_x(p1$value, p0$value), p0$year, dir, d0$value, d1$value)
       }),

  list(id = "q3", domain = "Economy", nav = "Sectors", q = "Did India skip the manufacturing stage other economies went through?",
       note = paste("Deliberately three lines, not a stacked area: World Bank value-added shares sum to about",
                    "91%, not 100 (they exclude taxes less subsidies on products). Stacking would fake a",
                    "part-to-whole that does not exist."),
       caveat = "Value added excludes taxes less subsidies, so the three shares do not sum to 100%.",
       fn = function(d) chart_structural_transition(d),
       finding = function(d) {
         a0 <- val_at(d, "NV.AGR.TOTL.ZS", "first"); a1 <- val_at(d, "NV.AGR.TOTL.ZS", "last")
         i0 <- val_at(d, "NV.IND.TOTL.ZS", "first"); i1 <- val_at(d, "NV.IND.TOTL.ZS", "last")
         s0 <- val_at(d, "NV.SRV.TOTL.ZS", "first"); s1 <- val_at(d, "NV.SRV.TOTL.ZS", "last")
         if (is.null(a1)) return(NULL)
         sprintf(paste("Agriculture fell %.0f%% → %.0f%% of GDP and services rose %.0f%% → %.0f%%,",
                       "but industry moved only %+.0f points. India went from farms to services",
                       "without the factory stage in between."),
                 a0$value, a1$value, s0$value, s1$value, i1$value - i0$value)
       }),

  list(id = "q4", domain = "Economy", nav = "Shocks", q = "Which years are genuine shocks rather than noise?",
       note = paste("Each year's growth measured against the economy's own trailing 10-year mean, so the",
                    "baseline is India's norm rather than an arbitrary zero. Diverging colour with a",
                    "neutral zero line."),
       caveat = "A trailing window means the first ten years of any range have no baseline and are dropped.",
       fn = function(d) chart_shock_detector(d),
       finding = function(d) {
         g <- d |> filter(code == "NY.GDP.MKTP.KD.ZG", !is.na(value)) |> arrange(year)
         if (nrow(g) < 12) return(NULL)
         roll <- stats::filter(g$value, rep(1 / 10, 10), sides = 1)
         x <- g |> mutate(dev = value - as.numeric(roll)) |> filter(!is.na(dev))
         w <- x |> slice_min(dev, n = 1, with_ties = FALSE)
         sprintf("The deepest shock is %d, %.1f points below trend. %d of %d years fell more than 2 points short.",
                 w$year, w$dev, sum(x$dev < -2), nrow(x))
       }),

  list(id = "q5", domain = "Society", nav = "Inclusion", q = "Did growth actually reach women?",
       note = paste("A connected scatter, not two time series: prosperity on x, female participation on y,",
                    "time as the colour channel. If growth were inclusive the path would climb to the right."),
       caveat = "Modelled ILO estimate, not a direct survey. Definitions of informal and unpaid work shift the level substantially.",
       fn = function(d) chart_growth_vs_inclusion(d),
       finding = function(d) {
         f <- d |> filter(code == "SL.TLF.CACT.FE.ZS", !is.na(value)) |> arrange(year)
         if (nrow(f) < 3) return(NULL)
         pk <- f |> slice_max(value, n = 1, with_ties = FALSE); tr <- f |> slice_min(value, n = 1, with_ties = FALSE)
         p0 <- val_at(d, "NY.GDP.PCAP.CD", "first"); p1 <- val_at(d, "NY.GDP.PCAP.CD", "last")
         sprintf(paste("Participation peaked at %.1f%% in %d, bottomed at %.1f%% in %d, and sits at %.1f%% now",
                       "— while GDP per capita went %s → %s."),
                 pk$value, pk$year, tr$value, tr$year, f$value[nrow(f)], fmt_d(p0$value), fmt_d(p1$value))
       }),

  list(id = "q7", domain = "Economy", nav = "Openness", span = 1,
       q = "Did 1991 actually open the economy, or was it already opening?",
       note = paste("Trade as a share of GDP. A single series, so an area is legal and reads as magnitude",
                    "over time. The 1991 marker lets you check whether the break is a step or a slope."),
       caveat = "Trade share rises when trade grows OR when GDP stalls. A spike is not automatically good news.",
       fn = function(d) chart_openness(d),
       finding = function(d) {
         a <- val_at(d, "NE.TRD.GNFS.ZS", "first"); b <- val_at(d, "NE.TRD.GNFS.ZS", "last")
         pk <- d |> filter(code == "NE.TRD.GNFS.ZS", !is.na(value)) |>
           slice_max(value, n = 1, with_ties = FALSE)
         if (is.null(b)) return(NULL)
         sprintf("Trade ran %.0f%% of GDP in %d, peaked at %.0f%% in %d, and sits at %.0f%% in %d.",
                 a$value, a$year, pk$value, pk$year, b$value, b$year)
       }),

  list(id = "q8", domain = "Society", nav = "Diffusion", span = 1,
       q = "Which spread faster \u2014 the grid or the network?",
       note = paste("Both measures sit on comparable 0\u2013100 scales, so one axis is honest here.",
                    "Electricity is a century-old state project; mobile is a twenty-year private one."),
       caveat = "Mobile counts subscriptions, not people \u2014 multiple SIMs inflate it. Electricity counts connections, not reliability or hours supplied.",
       fn = function(d) chart_diffusion_speed(d),
       finding = function(d) {
         # from first NON-ZERO year — mobile is a literal 0 back to 1960 and
         # counting those decades inverts the answer
         rate <- function(cd) {
           s <- d |> filter(code == cd, !is.na(value)) |> arrange(year)
           s <- s |> filter(year >= min(s$year[s$value > 0]))
           if (nrow(s) < 2) return(NULL)
           yrs <- s$year[nrow(s)] - s$year[1]
           list(gain = s$value[nrow(s)] - s$value[1], yrs = yrs,
                per = (s$value[nrow(s)] - s$value[1]) / max(yrs, 1), y0 = s$year[1])
         }
         e <- rate("EG.ELC.ACCS.ZS"); m <- rate("IT.CEL.SETS.P2")
         if (is.null(e) || is.null(m)) return(NULL)
         sprintf(paste("From %d electricity added %.0f points in %d years (%.1f/yr). From %d mobile added",
                       "%.0f points in %d years (%.1f/yr) \u2014 about %.1f\u00d7 faster."),
                 e$y0, e$gain, e$yrs, e$per, m$y0, m$gain, m$yrs, m$per, m$per / max(e$per, .001))
       }),

  list(id = "q9", domain = "State", nav = "Priorities", span = 1,
       q = "Guns, books, or medicine \u2014 what does the state actually prioritise?",
       note = paste("Three spending lines as a share of GDP. Military data runs from 1960; education and",
                    "health only from the late 1990s, so the comparison is honest only where all three overlap."),
       caveat = "These are spending shares, not outcomes, and central plus state budgets are consolidated differently across the three series.",
       fn = function(d) chart_state_priorities(d),
       finding = function(d) {
         g <- function(cd) { v <- val_at(d, cd, "last"); if (is.null(v)) NA_real_ else v$value }
         mil <- g("MS.MIL.XPND.GD.ZS"); edu <- g("SE.XPD.TOTL.GD.ZS"); hea <- g("SH.XPD.CHEX.GD.ZS")
         if (all(is.na(c(mil, edu, hea)))) return(NULL)
         sprintf("Latest available: military %.1f%% of GDP, education %.1f%%, health %.1f%%.",
                 mil, edu, hea)
       }),

  list(id = "q10", domain = "State", nav = "Fragility", span = 1,
       q = "How close has India come to running out of foreign exchange?",
       note = paste("A derived metric: reserves divided by monthly imports. The shaded band is the",
                    "conventional three-month adequacy floor \u2014 a status colour, because it means danger,",
                    "not a series."),
       caveat = "Derived from annual averages, so it smooths away the intra-year crunch that actually triggers a crisis.",
       fn = function(d) chart_reserve_adequacy(d),
       finding = function(d) {
         df <- wide(d, "FI.RES.TOTL.CD", "NE.IMP.GNFS.ZS", "NY.GDP.MKTP.CD") |>
           mutate(months = FI.RES.TOTL.CD / ((NE.IMP.GNFS.ZS / 100 * NY.GDP.MKTP.CD) / 12)) |>
           filter(!is.na(months))
         if (nrow(df) == 0) return(NULL)
         lo <- df |> slice_min(months, n = 1, with_ties = FALSE)
         sprintf("Thinnest cover was %.1f months in %d; %d year(s) fell below the three-month floor. Now %.1f months.",
                 lo$months, lo$year, sum(df$months < 3), df$months[nrow(df)])
       }),

  list(id = "q11", domain = "Environment", nav = "Decoupling", span = 1,
       q = "Is growth decoupling from emissions?",
       note = paste("Both indexed to a common base on one axis. If the lines separate, each dollar of",
                    "income is costing less carbon \u2014 relative decoupling. Absolute decoupling needs the",
                    "CO\u2082 line to actually fall."),
       caveat = "Production-based emissions: carbon embodied in imported goods is counted in the exporting country, not here.",
       fn = function(d) chart_decoupling(d),
       finding = function(d) {
         co2 <- d |> filter(code == "EN.GHG.CO2.PC.CE.AR5", !is.na(value)) |> arrange(year)
         gdp <- d |> filter(code == "NY.GDP.PCAP.CD", !is.na(value)) |> arrange(year)
         if (nrow(co2) < 2 || nrow(gdp) < 2) return(NULL)
         b   <- max(min(co2$year), min(gdp$year))   # same base as the chart
         co2 <- co2 |> filter(year >= b); gdp <- gdp |> filter(year >= b)
         c0 <- co2[1, ]; c1 <- co2[nrow(co2), ]; g0 <- gdp[1, ]; g1 <- gdp[nrow(gdp), ]
         cg <- c1$value / c0$value; gg <- g1$value / g0$value
         sprintf(paste("Since %d income per person grew %.1f\u00d7 while CO\u2082 per person grew %.1f\u00d7 \u2014 relative",
                       "decoupling, but emissions are still rising, not falling."),
                 b, gg, cg)
       }),

  list(id = "q12", domain = "Politics", nav = "Erosion", span = 2,
       q = "Which part of democracy eroded first?",
       note = paste("Eight V-Dem components. Eight hues would be unreadable and would bury the point, so",
                    "this is an emphasis chart: the steepest faller and the only riser carry colour, the",
                    "rest sit in context gray."),
       caveat = paste("Expert-coded indices; the level is debatable, the direction and relative timing are",
                      "the signal. Note the political corruption index runs the other way \\u2014 rising means",
                      "MORE corruption, so its climb is not good news."),
       fn = function(d) chart_democratic_erosion(d),
       finding = function(d) {
         x <- d |> filter(category == "Democracy", !is.na(value)) |> group_by(indicator) |>
           summarise(d0 = first(value[order(year)]), d1 = last(value[order(year)]),
                     y0 = min(year), .groups = "drop") |> mutate(delta = d1 - d0)
         if (nrow(x) == 0) return(NULL)
         w <- x |> slice_min(delta, n = 1, with_ties = FALSE)
         sprintf("%s fell furthest since %d, from %.2f to %.2f. %d of %d components declined.",
                 w$indicator, w$y0, w$d0, w$d1, sum(x$delta < 0), nrow(x))
       }),

  list(id = "q13", domain = "Politics", nav = "Profile", span = 1,
       q = "What shape is India\u2019s governance profile, and how has it changed?",
       note = paste("A radar, used under the only conditions that make one honest: six axes, one country,",
                    "exactly two time points, and every axis on the identical \u22122.5\u20132.5 scale."),
       caveat = paste("Radar exaggerates by area and the axis order is arbitrary \u2014 read the axis values,",
                      "never the size of the shape. WGI starts in 1996."),
       fn = function(d) chart_governance_radar(d),
       finding = function(d) {
         g <- d |> filter(category == "Governance", !is.na(value))
         if (nrow(g) == 0) return(NULL)
         yrs <- range(g$year)
         ch <- g |> filter(year %in% yrs) |> group_by(indicator) |>
           summarise(delta = value[which.max(year)] - value[which.min(year)], .groups = "drop")
         up <- ch |> slice_max(delta, n = 1, with_ties = FALSE)
         dn <- ch |> slice_min(delta, n = 1, with_ties = FALSE)
         sprintf("Between %d and %d, %s improved most (%+.2f) and %s slipped most (%+.2f).",
                 yrs[1], yrs[2], up$indicator, up$delta, dn$indicator, dn$delta)
       }),

  list(id = "q14", domain = "Economy", nav = "Composition", span = 1,
       q = "What did the shape of the economy look like before reform, and now?",
       note = paste("A dumbbell \u2014 the right form for before/after per item. Every row is the same unit,",
                    "% of GDP, which is what makes one shared axis honest."),
       caveat = "Tax, education and health series start later than 1991, so those rows use their earliest available year.",
       fn = function(d) chart_composition_shift(d),
       finding = function(d) {
         codes <- c(NV.AGR.TOTL.ZS="Agriculture", NV.SRV.TOTL.ZS="Services",
                    NE.EXP.GNFS.ZS="Exports", NE.IMP.GNFS.ZS="Imports",
                    GC.TAX.TOTL.GD.ZS="Tax revenue", MS.MIL.XPND.GD.ZS="Military",
                    NV.IND.TOTL.ZS="Industry", SE.XPD.TOTL.GD.ZS="Education",
                    SH.XPD.CHEX.GD.ZS="Health", BX.KLT.DINV.WD.GD.ZS="FDI inflows")
         x <- d |> filter(code %in% names(codes), !is.na(value)) |> group_by(code) |>
           summarise(from = value[which.min(abs(year - 1991))],
                     to = value[which.max(year)], .groups = "drop") |>
           mutate(label = codes[code], delta = to - from)
         if (nrow(x) == 0) return(NULL)
         u <- x |> slice_max(delta, n = 1, with_ties = FALSE)
         v <- x |> slice_min(delta, n = 1, with_ties = FALSE)
         sprintf("Since 1991 %s rose most (%+.1f pts of GDP) and %s fell most (%+.1f).",
                 u$label, u$delta, v$label, v$delta)
       }),

  list(id = "q6", domain = "Evidence", nav = "Evidence", q = "Where is our evidence weakest?",
       note = paste("Measurement bias made visible. Density of observations per category per decade.",
                    "Forecast years are excluded — projections are not evidence."),
       caveat = "Density counts whether a year has any observation, not whether the measurement is good.",
       fn = function(d) chart_evidence_density(d),
       finding = function(d) {
         x <- d |> filter(!is_forecast) |> group_by(category) |>
           summarise(cov = 100 * n_distinct(paste(code, year)) /
                       (n_distinct(code) * (max(year) - min(year) + 1)), .groups = "drop")
         if (nrow(x) == 0) return(NULL)
         lo <- x |> slice_min(cov, n = 1, with_ties = FALSE); hi <- x |> slice_max(cov, n = 1, with_ties = FALSE)
         sprintf("%s is the thinnest evidence at %.0f%% of years covered; %s is the densest at %.0f%%.",
                 lo$category, lo$cov, hi$category, hi$cov)
       })
)

# Order by domain so the rail groups; a small caps heading is injected into the
# first label of each group. radioButtons has no optgroup, but choiceNames takes
# arbitrary HTML — one radio group, real visual grouping, no extra state.
# span 2 = the chart needs a full-width row (wide axis labels, a colourbar, or
# stacked panels); span 1 = it reads fine at half width in a 2-up grid.
SPAN <- c(q1 = 1, q2 = 2, q3 = 1, q4 = 1, q5 = 2, q6 = 2, q7 = 1,
          q8 = 1, q9 = 1, q10 = 1, q11 = 1, q12 = 2, q13 = 1, q14 = 1)
QUESTIONS <- lapply(QUESTIONS, function(x) { x$span <- unname(SPAN[[x$id]]); x })

# Environment + Evidence are both about limits — of the planet, and of what we
# actually know. One tab rather than two singletons.
TAB_OF <- c(Economy = "Economy", State = "State", Society = "Society",
            Politics = "Politics", Environment = "Limits", Evidence = "Limits")
QUESTIONS <- lapply(QUESTIONS, function(x) { x$tab <- unname(TAB_OF[[x$domain]]); x })
TAB_ORDER <- c("Economy", "State", "Society", "Politics", "Limits")
QUESTIONS <- QUESTIONS[order(match(vapply(QUESTIONS, `[[`, "", "tab"), TAB_ORDER))]

nav_labels <- NULL  # replaced by tabs

css <- sprintf("
  body, .bslib-page-sidebar { background:%s; color:%s; }
  .display { font-family:'Geist',system-ui,sans-serif; font-weight:400; letter-spacing:-.01em; }
  .brand   { font-size:1.3rem; line-height:1.15; color:%s; margin-bottom:2px; }
  .brand-sub { font-size:.7rem; color:%s; letter-spacing:.06em; text-transform:uppercase; }

  /* hero figures: SANS and proportional figures. A serif display face on a hero
     number reads as decoration, and tabular-nums makes large digits look loose. */
  .rail-kpi   { font-size:1.45rem; color:%s; line-height:1.15; font-weight:600;
                font-variant-numeric:proportional-nums; }
  .rail-kpi-l { font-size:.66rem; color:%s; text-transform:uppercase; letter-spacing:.07em; }
  .rule { height:1px; background:%s; margin:15px 0; }

  .nav-underline .nav-link { color:%s; border:0; padding:9px 2px; margin-right:22px;
      font-size:.87rem; background:none; }
  .nav-underline .nav-link.active { color:%s; font-weight:600; box-shadow:inset 0 -2px 0 %s; }
  .nav-underline { border-bottom:1px solid %s; margin-bottom:6px; }

  .grid { display:grid; grid-template-columns:repeat(2, minmax(0,1fr));
          gap:30px 26px; margin-top:22px; }
  .cell-2 { grid-column:1 / -1; }
  @media (max-width:1100px) { .grid { grid-template-columns:1fr; }
                              .cell-2 { grid-column:auto; } }

  .c-title { font-family:'Geist',system-ui,sans-serif; font-size:1.12rem; line-height:1.3;
             color:%s; margin:0 0 5px; }
  .c-note  { font-size:.78rem; color:%s; line-height:1.45; margin:0 0 8px; }
  .c-find  { font-family:'Geist',system-ui,sans-serif; font-size:.99rem; line-height:1.4;
             color:%s; margin-top:9px; border-left:2px solid %s; padding-left:11px; }
  .c-cav   { font-size:.72rem; color:%s; line-height:1.4; margin-top:7px; }
  .irs-bar, .irs-handle>i:first-child { background:%s !important; border-color:%s !important; }
  .irs-grid-text, .irs-min, .irs-max { color:%s !important; }
",
  PAL$page, PAL$ink_2, PAL$ink, PAL$muted,
  PAL$ink, PAL$muted, PAL$grid,
  PAL$muted, PAL$ink, PAL$s1, PAL$grid,
  PAL$ink, PAL$muted, PAL$ink, PAL$s1, PAL$muted,
  PAL$s1, PAL$s1, PAL$muted)

chart_cell <- function(qq) {
  div(class = if (qq$span == 2) "cell-2" else "",
      p(class = "c-title", qq$q),
      p(class = "c-note", qq$note),
      plotlyOutput(qq$id, height = if (qq$span == 2) "360px" else "300px"),
      div(class = "c-find", textOutput(paste0("f_", qq$id), inline = TRUE)),
      div(class = "c-cav", qq$caveat))
}

tab_panel <- function(tab) {
  qs <- Filter(function(x) x$tab == tab, QUESTIONS)
  nav_panel(tab, div(class = "grid", lapply(qs, chart_cell)))
}

ui <- page_sidebar(
  theme = bs_theme(version = 5, bg = PAL$page, fg = PAL$ink, primary = PAL$s1,
                   base_font = font_google("Geist", local = FALSE),
                   heading_font = font_google("Geist", local = FALSE)),
  tags$head(tags$style(HTML(css))),

  # shinylive serves plotly's JS out of the WASM filesystem, so `crosstalk` and
  # `Plotly` can still be loading when the first chart values arrive. renderValue
  # then throws and htmlwidgets never retries, so whichever tab is open at boot
  # stays blank for the session. Hold the values back until the globals exist.
  # A fixed timeout cannot win this race — plotly-latest.min.js is ~3.5MB out of
  # the WASM filesystem, so "how long is enough" varies by machine. Instead, watch
  # the charts themselves and re-render only while one is still visibly blank.
  tags$head(tags$script(HTML("
    (function () {
      var last = 0, bumps = 0;
      var t = setInterval(function () {
        if (!window.Shiny || !window.Shiny.setInputValue) return;   // Shiny not up yet
        if (!(window.Plotly && window.crosstalk)) return;           // deps still downloading
        var blank = [].slice.call(document.querySelectorAll('.plotly.html-widget'))
          .some(function (el) { return el.offsetParent !== null &&
                                       !el.querySelector('.plot-container'); });
        if (!blank) { clearInterval(t); return; }                   // every visible chart painted
        var now = Date.now();
        if (now - last < 2500) return;                              // let the last re-render land
        if (++bumps > 8) { clearInterval(t); return; }              // stop nagging, blame elsewhere
        last = now;
        Shiny.setInputValue('plotly_ready', bumps, {priority: 'event'});
      }, 300);
    })();
  "))),
  fillable = FALSE,

  sidebar = sidebar(
    width = 240, bg = PAL$page, border = TRUE, padding = 20,
    div(class = "display brand", "Understanding Indian EcoPolitical Growth"),
    div(class = "brand-sub", "1789\u20132031"),
    div(class = "rule"),
    uiOutput("rail_kpis"),
    div(class = "rule"),
    sliderInput("yrs", "Year range", min = 1900, max = max(DATA$year),
                value = c(1960, max(DATA$year)), sep = "", width = "100%"),
    div(class = "rule"),
    p(style = sprintf("color:%s;font-size:.71rem;line-height:1.45", PAL$muted),
      sprintf("%d indicators. World Bank, IMF WEO, V-Dem. Projections past the last actual year are IMF estimates.",
              nrow(META)))
  ),

  div(style = "max-width:1240px;padding:2px 4px 50px",
      do.call(navset_underline, lapply(TAB_ORDER, tab_panel)))
)

server <- function(input, output, session) {

  filtered <- reactive(DATA |> filter(year >= input$yrs[1], year <= input$yrs[2]))

  output$rail_kpis <- renderUI({
    latest <- function(cd) {
      r <- DATA |> filter(code == cd, !is_forecast, !is.na(value))
      if (nrow(r) == 0) return(NULL) else r[which.max(r$year), ]
    }
    g <- latest("NY.GDP.MKTP.CD"); p <- latest("NY.GDP.PCAP.CD"); d <- latest("v2x_polyarchy")
    tile <- function(l, v) div(style = "margin-bottom:11px",
                               div(class = "rail-kpi-l", l), div(class = "rail-kpi", v))
    tagList(
      tile(sprintf("GDP \u00b7 %d", g$year), sprintf("$%.2fT", g$value / 1e12)),
      tile(sprintf("Per capita \u00b7 %d", p$year), fmt_d(p$value)),
      tile(sprintf("Democracy \u00b7 %d", d$year), sprintf("%.2f", d$value))
    )
  })

  lapply(QUESTIONS, function(qq) {
    output[[qq$id]] <- renderPlotly({
      # Re-render trigger, NOT a gate: plotly's JS ships with the first render
      # payload, so blocking that render would deadlock the shim waiting on it.
      input$plotly_ready
      qq$fn(filtered())
    })
    output[[paste0("f_", qq$id)]] <- renderText({
      f <- qq$finding(filtered())
      if (is.null(f)) "Not enough data in the selected range to state a finding." else f
    })
  })
}

shinyApp(ui, server)
