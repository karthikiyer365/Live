# Chart tokens + shared plotly styling.
#
# Dark is NOT an inverted light theme — it is its own set of steps chosen from
# the same ramps and validated against the dark surface. Both modes were run
# through the dataviz validator:
#
#   light  cat 1-3 vs #f9f9f7 : CVD dE 9.2 (deutan), normal 27.6  PASS
#                               (page is now #fff — contrast only rises)
#                               aqua #1baf7a 2.67:1 -> WARN, labels required
#   dark   cat 1-3 vs #1a1a19 : CVD dE 9.4 (deutan), normal 26.5  PASS
#                               all three clear 3:1                PASS
#   dark   sequential ramp    : monotone L, adjacent dL >= .06,
#                               single hue (4 deg spread)          PASS
#
# Flip the whole app with this one constant.
MODE <- "light"  # white site shell (site/index.html) — matches writing.karthikiyer.info

.pal <- list(
  light = list(
    s1 = "#2a78d6", s2 = "#eb6834", s3 = "#1baf7a", s4 = "#eda100",
    div_pos = "#2a78d6", div_neg = "#eb6834",
    seq = c("#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"),
    surface = "#fcfcfb", page = "#ffffff", panel = "#ffffff",
    ink = "#0b0b0b", ink_2 = "#52514e", muted = "#898781",
    grid = "#e1e0d9", baseline = "#c3c2b7", gray_ctx = "#c3c2b7",
    hover_bg = "#ffffff", hairline = "rgba(11,11,11,0.10)",
    st_good = "#0ca30c", st_critical = "#d03b3b",
    accent = "#d07"  # UI chrome only (tabs, slider): pink from karthikiyer.info; data keeps s1-s4
  ),
  dark = list(
    s1 = "#3987e5", s2 = "#d95926", s3 = "#199e70", s4 = "#c98500",
    div_pos = "#3987e5", div_neg = "#d95926",
    # reversed for a dark surface: dimmest step sits nearest the background,
    # brightest reads as "most". Never darker than step 600 on dark.
    seq = c("#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", "#b7d3f6", "#cde2fb"),
    surface = "#1a1a19", page = "#0d0d0d", panel = "#161615",
    ink = "#ffffff", ink_2 = "#c3c2b7", muted = "#898781",
    grid = "#2c2c2a", baseline = "#383835", gray_ctx = "#5a5a55",
    hover_bg = "#242423", hairline = "rgba(255,255,255,0.10)",
    st_good = "#0ca30c", st_critical = "#d03b3b",
    accent = "#d07"  # UI chrome only (tabs, slider): pink from karthikiyer.info; data keeps s1-s4
  )
)

PAL <- .pal[[MODE]]

# Recessive chrome: hairline solid grid (never dashed — dashing reads as
# "projection" when it is just a grid), muted axes, generous padding.
style_plot <- function(p, ylab = "", xlab = "", legend = TRUE, hovermode = "x unified",
                       margin = list(l = 58, r = 22, t = 26, b = 40)) {
  plotly::layout(
    p,
    # borderless: the plot sits directly on the page plane
    paper_bgcolor = "rgba(0,0,0,0)",
    plot_bgcolor  = "rgba(0,0,0,0)",
    font   = list(family = "Geist, system-ui, -apple-system, Segoe UI, sans-serif",
                  size = 12, color = PAL$ink_2),
    margin = margin,
    hovermode = hovermode,
    hoverlabel = list(bgcolor = PAL$hover_bg, bordercolor = PAL$baseline,
                      font = list(color = PAL$ink, size = 12)),
    xaxis = list(title = list(text = xlab, standoff = 10),
                 gridcolor = PAL$grid, griddash = "solid", zeroline = FALSE,
                 linecolor = PAL$baseline, tickcolor = PAL$baseline,
                 tickfont = list(color = PAL$muted, size = 11)),
    yaxis = list(title = list(text = ylab, standoff = 12),
                 gridcolor = PAL$grid, griddash = "solid", zeroline = FALSE,
                 linecolor = PAL$baseline, tickcolor = PAL$baseline,
                 tickfont = list(color = PAL$muted, size = 11)),
    legend = list(orientation = "h", x = 0, y = 1.16,
                  bgcolor = "rgba(0,0,0,0)",
                  font = list(color = PAL$ink_2, size = 11)),
    showlegend = legend
  ) |>
    plotly::config(displayModeBar = FALSE, responsive = TRUE)
}

# plotly wants a fraction/colour list for a continuous ramp
seq_scale <- function() {
  n <- length(PAL$seq)
  lapply(seq_len(n), function(i) list((i - 1) / (n - 1), PAL$seq[i]))
}

LINE_W  <- 2
MARK_SZ <- 8
