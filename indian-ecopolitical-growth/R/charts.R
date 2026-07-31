# Six charts, one analytical question each.
#
# Rules enforced here (see docs/CHART_RATIONALE.md):
#   - NO dual-axis anywhere. Two measures of different scale are indexed to a
#     common base (=100) on ONE axis. This is the #1 charting mistake.
#   - Colour follows the entity, never its rank — a filter never repaints series.
#   - Sequential = one hue light->dark. Diverging = warm/cool + NEUTRAL midpoint.
#   - Legend for >=2 series; direct labels selective, never a number per point.

suppressPackageStartupMessages({
  library(dplyr)
  library(tidyr)
  library(plotly)
})

series <- function(d, cd) d |> filter(code == cd) |> arrange(year)

# Index a series to 100 at the first year >= base present in the data.
index_to <- function(df, base_year) {
  b <- df |> filter(year >= base_year) |> slice(1) |> pull(value)
  if (length(b) == 0 || is.na(b) || b == 0) return(mutate(df, idx = NA_real_))
  mutate(df, idx = 100 * value / b)
}

# --- Q1 ------------------------------------------------------------------
# "Does headline GDP flatter what actually reached each person?"
# Both measures are money but differ by ~3 orders of magnitude, so they are
# INDEXED to a common base rather than given two axes.
chart_growth_inflection <- function(d, base_year = 1960) {
  gdp <- series(d, "NY.GDP.MKTP.CD")  |> index_to(base_year) |> mutate(k = "Total GDP")
  pc  <- series(d, "NY.GDP.PCAP.CD")  |> index_to(base_year) |> mutate(k = "GDP per capita")
  df  <- bind_rows(gdp, pc) |> filter(!is.na(idx))

  plot_ly(df, x = ~year, y = ~idx, color = ~k, colors = c("GDP per capita" = PAL$s2, "Total GDP" = PAL$s1),
          type = "scatter", mode = "lines", line = list(width = LINE_W),
          hovertemplate = "%{y:.0f}<extra>%{fullData.name}</extra>") |>
    layout(yaxis = list(type = "log")) |>
    style_plot(ylab = sprintf("Index (%d = 100, log scale)", base_year), xlab = NULL)
}

# --- Q2 ------------------------------------------------------------------
# "Do prosperity and democratic depth move together, or diverge?"
# SMALL MULTIPLES, not one shared axis. V-Dem is a bounded 0-1 index; GDP per
# capita grew ~70x. Indexing both to 100 and log-scaling flattens democracy into
# a straight line — technically not dual-axis, but it hides the answer. Two
# stacked panels share the x axis and each keeps its natural scale.
chart_democracy_vs_prosperity <- function(d, base_year = 1960) {
  pc  <- series(d, "NY.GDP.PCAP.CD") |> filter(year >= base_year)
  dem <- series(d, "v2x_polyarchy")  |> filter(year >= base_year)

  mark_1991 <- list(type = "line", x0 = 1991, x1 = 1991, y0 = 0, y1 = 1,
                    yref = "paper", line = list(color = PAL$baseline, width = 1))

  p_top <- plot_ly(dem, x = ~year, y = ~value, type = "scatter", mode = "lines",
                   line = list(width = LINE_W, color = PAL$s1),
                   name = "Electoral democracy (V-Dem)",
                   hovertemplate = "%{y:.2f}<extra>Democracy</extra>") |>
    layout(yaxis = list(title = list(text = "V-Dem 0–1", standoff = 14), range = c(0, 1)))

  p_bot <- plot_ly(pc, x = ~year, y = ~value, type = "scatter", mode = "lines",
                   line = list(width = LINE_W, color = PAL$s2),
                   name = "GDP per capita",
                   hovertemplate = "$%{y:,.0f}<extra>GDP per capita</extra>") |>
    layout(yaxis = list(title = list(text = "US$ (log)", standoff = 14),
                        type = "log", dtick = 1))

  subplot(p_top, p_bot, nrows = 2, shareX = TRUE, titleY = TRUE, margin = 0.07) |>
    layout(shapes = list(mark_1991, modifyList(mark_1991, list(yref = "y2"))),
           annotations = list(list(x = 1991, y = 1.03, yref = "paper", text = "1991 liberalisation",
                                   showarrow = FALSE, xanchor = "left",
                                   font = list(size = 11, color = PAL$muted)))) |>
    style_plot(ylab = NULL, xlab = NULL)
}

# --- Q3 ------------------------------------------------------------------
# "Did India skip the manufacturing stage every other economy went through?"
# NOT a stacked area: WB value-added shares sum to ~91%, not 100 (they exclude
# taxes less subsidies on products). Stacking would fake a part-to-whole.
chart_structural_transition <- function(d) {
  df <- d |>
    filter(code %in% c("NV.AGR.TOTL.ZS", "NV.IND.TOTL.ZS", "NV.SRV.TOTL.ZS")) |>
    mutate(k = recode(code,
                      NV.AGR.TOTL.ZS = "Agriculture",
                      NV.IND.TOTL.ZS = "Industry",
                      NV.SRV.TOTL.ZS = "Services")) |>
    arrange(year)

  # direct-label each line at its last point (also satisfies the aqua contrast WARN)
  ends <- df |> group_by(k) |> filter(year == max(year)) |> ungroup()

  plot_ly(df, x = ~year, y = ~value, color = ~k,
          colors = c(Agriculture = PAL$s3, Industry = PAL$s2, Services = PAL$s1),
          type = "scatter", mode = "lines", line = list(width = LINE_W),
          hovertemplate = "%{y:.1f}%<extra>%{fullData.name}</extra>") |>
    add_annotations(data = ends, x = ~year, y = ~value, text = ~k,
                    xanchor = "left", xshift = 6, showarrow = FALSE,
                    font = list(size = 12, color = PAL$ink_2), inherit = FALSE) |>
    style_plot(ylab = "% of GDP (value added)", xlab = NULL, legend = FALSE)
}

# --- Q4 ------------------------------------------------------------------
# "Which years are genuine shocks rather than noise?"  THE anomaly chart.
# Deviation of annual growth from its own trailing 10-year mean, so the
# baseline is the economy's own norm, not an arbitrary zero.
chart_shock_detector <- function(d, window = 10) {
  g <- series(d, "NY.GDP.MKTP.KD.ZG")
  roll <- stats::filter(g$value, rep(1 / window, window), sides = 1)
  df <- g |> mutate(trend = as.numeric(roll), dev = value - trend) |> filter(!is.na(dev))

  plot_ly(df, x = ~year, y = ~dev, type = "bar",
          marker = list(color = ~ifelse(dev >= 0, PAL$div_pos, PAL$div_neg),
                        line = list(width = 0)),
          hovertemplate = paste0("%{x}<br>growth %{customdata:.1f}%",
                                 "<br>vs 10y trend: %{y:+.1f} pts<extra></extra>"),
          customdata = ~value) |>
    layout(yaxis = list(zeroline = TRUE, zerolinecolor = PAL$baseline, zerolinewidth = 1),
           bargap = 0.35) |>
    style_plot(ylab = sprintf("GDP growth vs trailing %dy mean (pts)", window),
               xlab = NULL, legend = FALSE, hovermode = "closest")
}

# --- Q5 ------------------------------------------------------------------
# "Did growth actually reach women?"  Connected scatter: prosperity on x,
# female labour participation on y, time as a single sequential hue. One
# series, so no legend — a colourbar carries the time channel.
chart_growth_vs_inclusion <- function(d) {
  df <- d |>
    filter(code %in% c("NY.GDP.PCAP.CD", "SL.TLF.CACT.FE.ZS")) |>
    select(year, code, value) |>
    pivot_wider(names_from = code, values_from = value) |>
    rename(gdp_pc = NY.GDP.PCAP.CD, flfp = SL.TLF.CACT.FE.ZS) |>
    filter(!is.na(gdp_pc), !is.na(flfp)) |>
    arrange(year)

  labs <- df |> filter(year %in% c(min(year), 2000, 2010, 2020, max(year)))

  plot_ly(df, x = ~gdp_pc, y = ~flfp, type = "scatter", mode = "lines+markers",
          line = list(color = PAL$gray_ctx, width = LINE_W),
          marker = list(size = MARK_SZ + 1, color = ~year, colorscale = seq_scale(),
                        line = list(color = PAL$surface, width = 2),  # 2px surface ring
                        colorbar = list(title = list(text = "Year", font = list(size = 11)),
                                        thickness = 10, outlinewidth = 0,
                                        tickfont = list(color = PAL$muted, size = 10))),
          hovertemplate = "%{marker.color}<br>$%{x:,.0f}<br>%{y:.1f}% female LFP<extra></extra>") |>
    add_annotations(data = labs, x = ~gdp_pc, y = ~flfp, text = ~year,
                    showarrow = FALSE, yshift = 15, inherit = FALSE,
                    font = list(size = 11, color = PAL$ink_2)) |>
    style_plot(ylab = "Female labour force participation (%)",
               xlab = "GDP per capita (current US$)", legend = FALSE, hovermode = "closest")
}

# --- Q6 ------------------------------------------------------------------
# "Where is our evidence weakest?"  Measurement bias made visible: we know
# least about inequality and poverty — exactly where it matters most.
# Sequential, one hue, light->dark.
chart_evidence_density <- function(d) {
  df <- d |>
    # Projections are not evidence. Including IMF forecast years would paint a
    # 2030s column and claim we have data we do not have.
    filter(!is_forecast) |>
    mutate(decade = 10 * (year %/% 10)) |>
    filter(decade >= 1960) |>
    group_by(category, decade) |>
    summarise(density = 100 * n_distinct(paste(code, year)) /
                        (n_distinct(code) * 10), .groups = "drop") |>
    mutate(density = pmin(density, 100))

  m <- df |> pivot_wider(names_from = decade, values_from = density) |> arrange(category)
  mat <- as.matrix(m[, -1])

  plot_ly(x = colnames(m)[-1], y = m$category, z = mat, type = "heatmap",
          colorscale = seq_scale(), zmin = 0, zmax = 100,
          xgap = 2, ygap = 2,   # 2px surface gap between cells, not borders
          hovertemplate = "%{y} · %{x}s<br>%{z:.0f}% of years covered<extra></extra>",
          colorbar = list(title = list(text = "% years", font = list(size = 11)),
                          thickness = 10, outlinewidth = 0,
                          tickfont = list(color = PAL$muted, size = 10))) |>
    style_plot(ylab = NULL, xlab = NULL, legend = FALSE, hovermode = "closest")
}

# plotly wants a fraction/colour list for a continuous ramp
seq_scale <- function() {
  n <- length(PAL$seq)
  lapply(seq_len(n), function(i) list((i - 1) / (n - 1), PAL$seq[i]))
}
