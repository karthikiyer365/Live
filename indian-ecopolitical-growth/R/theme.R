# Chart tokens + shared plotly styling.
#
# Palette is the validated reference instance — do not hand-pick hexes elsewhere.
# Categorical slots 1-3 were run through the dataviz validator:
#   light: CVD worst-adjacent dE 9.2 (deutan), normal 27.6  -> PASS
#   dark:  CVD worst-adjacent dE 9.4 (deutan), normal 26.5  -> PASS
# Light-mode aqua (#1baf7a) sits at 2.74:1 vs surface -> WARN, which obligates
# visible labels. Every chart using slot 3 direct-labels its series.

PAL <- list(
  s1 = "#2a78d6",  # blue
  s2 = "#eb6834",  # orange
  s3 = "#1baf7a",  # aqua
  s4 = "#eda100",  # yellow

  # diverging pair: warm/cool poles + NEUTRAL GRAY midpoint (never a hue at 0)
  div_pos = "#2a78d6",
  div_neg = "#eb6834",
  div_mid = "#f0efec",

  # sequential, one hue light->dark (steps 100..700 of the blue ramp)
  seq = c("#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"),

  surface   = "#fcfcfb",
  ink       = "#0b0b0b",
  ink_2     = "#52514e",
  muted     = "#898781",
  grid      = "#e1e0d9",
  baseline  = "#c3c2b7",
  gray_ctx  = "#c3c2b7"   # de-emphasis gray for emphasis charts
)

# Recessive chrome: hairline solid grid (never dashed — dashing reads as
# "projection" when it is just a grid), muted axes, generous padding.
style_plot <- function(p, ylab = "", xlab = "", legend = TRUE, hovermode = "x unified") {
  plotly::layout(
    p,
    paper_bgcolor = PAL$surface,
    plot_bgcolor  = PAL$surface,
    font   = list(family = "system-ui, -apple-system, Segoe UI, sans-serif",
                  size = 13, color = PAL$ink_2),
    margin = list(l = 62, r = 28, t = 34, b = 48),
    hovermode = hovermode,
    hoverlabel = list(bgcolor = PAL$surface, bordercolor = PAL$baseline,
                      font = list(color = PAL$ink, size = 12)),
    xaxis = list(title = list(text = xlab, standoff = 12),
                 gridcolor = PAL$grid, griddash = "solid", zeroline = FALSE,
                 linecolor = PAL$baseline, tickcolor = PAL$baseline,
                 tickfont = list(color = PAL$muted)),
    yaxis = list(title = list(text = ylab, standoff = 14),
                 gridcolor = PAL$grid, griddash = "solid", zeroline = FALSE,
                 linecolor = PAL$baseline, tickcolor = PAL$baseline,
                 tickfont = list(color = PAL$muted)),
    legend = list(orientation = "h", x = 0, y = 1.14,
                  bgcolor = "rgba(0,0,0,0)",
                  font = list(color = PAL$ink_2, size = 12)),
    showlegend = legend
  ) |>
    plotly::config(displayModeBar = FALSE, responsive = TRUE)
}

# 2px lines, >=8px markers — thin marks, not heavy blocks.
LINE_W  <- 2
MARK_SZ <- 8
