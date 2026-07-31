# Chart rationale — the questions, and why each form was chosen

_Twelve charts across six domains. Each answers one question about trend, bias, weakness, or anomaly.
Palette validated with the dataviz validator; no chart uses a second y-axis. The full domain question
list, including rejected questions, is in `QUESTION_BANK.md`._

## The questions

A dashboard that just plots indicators answers nothing. These six were picked because each one exposes
something the raw series hides.

| # | Question | What it exposes | Form | Colour job |
|---|---|---|---|---|
| Q1 | Does headline GDP flatter what reached each person? | **Bias** — aggregate growth absorbs population growth | Indexed multi-line, log | 2 categorical |
| Q2 | Do prosperity and democratic depth move together? | **Trend divergence** — the core eco-political claim | Small multiples | 2 categorical |
| Q3 | Did India skip the manufacturing stage? | **Structural weakness** — agri → services, industry flat | Multi-line | 3 categorical |
| Q4 | Which years are genuine shocks, not noise? | **Anomalies** — 1991, 2008, 2020 against India's own norm | Diverging bar | diverging |
| Q5 | Did growth actually reach women? | **Bias** — participation fell while GDP rose | Connected scatter | sequential (time) |
| Q6 | Where is our evidence weakest? | **Measurement bias** — thinnest data on inequality | Heatmap | sequential |

### Second set (Q7–Q12)

| # | Domain | Question | Form | Colour job |
|---|---|---|---|---|
| Q7 | Trade | Did 1991 actually open the economy? | Area (single series) | 1 hue |
| Q8 | Society | Which spread faster — grid or network? | Multi-line | 2 categorical |
| Q9 | State | Guns, books, or medicine? | Multi-line + markers | 3 categorical |
| Q10 | State | How close to running out of foreign exchange? | Line + threshold band | 1 hue + **status** |
| Q11 | Environment | Is growth decoupling from emissions? | Indexed multi-line | 2 categorical |
| Q12 | Politics | Which part of democracy eroded first? | **Emphasis** (8 series) | 2 hues + gray |

**Q12 is why emphasis exists.** Eight V-Dem components is past the categorical ceiling, and eight hues
would be unreadable *and* bury the point. The steepest faller and the only riser carry colour; the other
six sit in context gray. Never solve "too many series" by generating more hues.

**Q10 is the only chart using status colour.** The 3-month adequacy floor means *danger*, not "series 2",
which is exactly the reserved use. Its label sits right-aligned because the left of the band is where the
1960s series actually runs.

## Form decisions that were not obvious

### Q1 & Q2 — the dual-axis trap

The instinct for "GDP vs democracy" is two y-axes. **That is the single most common charting mistake:**
the alignment of two scales is arbitrary, so the chart invents a correlation that isn't in the data.

Q1 solves it by **indexing** — both measures are money, both to 100 at 1960, one axis.

Q2 could not use the same trick. V-Dem is a *bounded* 0–1 index; GDP per capita grew ~70×. Indexing both
to 100 and log-scaling is technically not dual-axis, but it flattens democracy into a near-straight line
— it hides the answer instead of showing it. First build did exactly this and the y-axis produced **ten
overlapping tick labels**, which is what made the flaw visible.

**Fix: small multiples.** Two stacked panels, shared x axis, each keeping its natural scale.

### Q3 — why not a stacked area

Sector shares look like a textbook part-to-whole. They aren't:

```
1960: 101.0%      1991: 91.9%      2023: 90.8%
```

World Bank value-added excludes taxes less subsidies on products, so the three sectors do **not** sum to
100. Stacking would fake a whole that doesn't exist and silently mis-state every segment. Three
lines instead — and the story (agriculture collapsing, services climbing, industry flat) reads better
as lines anyway.

### Q4 — baseline is India's own norm

Deviation is measured against a **trailing 10-year mean**, not against zero and not against a global
average. "Bad year" should mean bad *for India*, not bad versus an arbitrary constant. Diverging colour
with a neutral zero line, warm/cool poles.

### Q5 — connected scatter, not two time series

Two lines would let a reader assume co-movement. Putting prosperity on x and participation on y forces
the actual relationship into view: if growth were inclusive, the path climbs right. It doesn't
monotonically — participation ran 30.3% (1990) → 34.4% (2000) → 28.4% (2010) → **26.0% (2020)** → 32.4%
(2024). Time is the colour channel; one series, so a colourbar replaces the legend.

### Q6 — the chart about the data itself

Density of observations per category per decade. The thin rows are inequality and poverty — the
questions people argue about hardest are the ones we have least evidence for. Worth stating plainly
rather than burying, since it bounds every claim the rest of the dashboard makes.

## Colour rules applied

- **Validated, not eyeballed.** Categorical slots 1–3 run through `validate_palette.js`:
  light CVD worst-adjacent ΔE 9.2 (deutan), normal 27.6 — PASS; dark ΔE 9.4 / 26.5 — PASS.
- Light-mode aqua (`#1baf7a`) sits at 2.74:1 against the surface → **WARN**, which obligates visible
  labels. Q3 direct-labels every line at its endpoint, satisfying it.
- **Colour follows the entity, never rank** — the year-range slider never repaints a series.
- Sequential = one hue light→dark (blue ramp, 7 steps). Diverging = warm/cool + **neutral** midpoint.
- Grid and axes are solid hairlines. Dashed gridlines read as "projection" when they're just a grid.
- Legend for ≥ 2 series; direct labels selective. Never a number on every point.

## Page layout — sidebar + focus

Six equal cards in one column read as a list, not an argument, and ran 3,300px tall with no hierarchy.
Replaced with a **sidebar + focus view**:

- **Left rail** — title, three live KPIs, the six questions as a persistent index, one year-range slider.
  The rail is the table of contents; you always know where you are and what else exists.
- **Right pane** — one question, one large chart (520px), then **Finding** and **Caveat** side by side.
- **No cards.** Charts render with a transparent background directly onto the page plane. The palette
  was re-validated against that surface (`--surface "#f9f9f7"`): all checks still PASS, aqua contrast
  moves 2.74 → 2.67 and remains a labels-required WARN.
- **Serif display type** (Newsreader) for the brand, questions, KPI figures and findings; sans (Inter)
  for notes, labels and all chart text.

### Findings are computed, never hardcoded

Each question carries a `finding()` that derives its sentence from the *visible* data, so it stays true
when the year range moves. A hardcoded sentence is a lie waiting to happen.

```
Q1  Total GDP grew 107× between 1960 and 2025. Per person, only 32× — population absorbed the rest.
Q2  GDP per capita rose 32× since 1960, while the democracy index fell from 0.67 to 0.38. They diverge.
Q3  Agriculture fell 42% → 16% of GDP and services rose 39% → 49%, but industry moved only +4 points.
Q4  The deepest shock is 2020, -11.0 points below trend. 9 of 56 years fell more than 2 points short.
Q5  Participation peaked at 34.9% in 2005, bottomed at 26.0% in 2020, and sits at 32.4% now.
Q6  Inequality is the thinnest evidence at 17% of years covered; Democracy is the densest at 100%.
```

⚠️ Every `slice_min`/`slice_max` needs `with_ties = FALSE`. Q6 originally tied three categories at 100%
coverage and `sprintf` vectorised it into three concatenated sentences.

## Verified in the browser

Rendered at 1200px and inspected programmatically (the validator checks colour, not layout):

```
horizontal overflow  : none
plots rendered       : 6/6, all with main-svg
tick/label collisions: 0   (was 10 on Q2 before the small-multiples fix)
nav switching        : all 6 questions render, findings recompute per question
```

Screenshot review caught two bugs the DOM checks structurally could not: KPI tiles stacking vertically
(a single `uiOutput` is ONE child, so `layout_columns` never split it) and a phantom 2030s column in the
evidence heatmap. Both fixed before this doc was written.

## Bugs the second set surfaced

| Bug | Cause | Fix |
|---|---|---|
| Q1 had 8 tick collisions | log axis drew minor tick labels (5,6,7,8,9) | `dtick = 1` — powers of ten only |
| Q8 concluded electricity spread *faster* | mobile is a literal `0` back to 1960, so diffusion looked 64 years slow | both series start at first **non-zero** year |
| Q11 said "since 1970", chart based at 1990 | chart had an internal year floor the finding didn't share | chart derives its base from the data; both read the same window |
| Q12 said "since 1960", chart based at 1990 | same class as above | internal floor removed |

The Q11/Q12 pair is the instructive one: any time a chart filters internally but its finding reads the
full range, **the text and the picture describe different periods**. Charts now take the window they are
given rather than imposing one.

## Third set (Q13–Q14) — beyond line charts

| # | Question | Form | Why this form |
|---|---|---|---|
| Q13 | What shape is India's governance profile? | **Radar** | Six axes, one country, two time points, one identical −2.5–2.5 scale |
| Q14 | What did the economy look like before reform, and now? | **Dumbbell** | The endorsed before→after form; every row is the same unit (% of GDP) |

**Radar is a judgment call, and only defensible under conditions that all hold here.** Radar lies when
axes carry different units, when there are too many axes to read, or when the enclosed *area* gets read
as a quantity. Mitigations applied: identical scale on every axis, only six axes, only two series, light
fills, and a finding that quotes axis values rather than area. The caveat says the axis order is
arbitrary and the area is not meaningful.

**Dumbbell needed no such argument** — it is the listed form for before/after per item, and restricting
the rows to `% of GDP` series is what makes one shared axis honest.

## Dark mode

`MODE <- "dark"` in `R/theme.R` flips the whole app. Dark is **not an inverted light theme** — it is its
own set of steps from the same ramps, validated against the dark surface:

```
dark cat 1-3 vs #1a1a19   CVD dE 9.4 (deutan), normal 26.5, all >= 3:1   PASS
dark sequential ramp      monotone L, adjacent dL >= .06, 4 deg hue      PASS
```

The sequential ramp is **reversed** for dark so the dimmest step sits nearest the background and the
brightest reads as "most", and never goes darker than step 600.

Verified live in the browser rather than assumed: rendered line strokes are `#d95926` / `#3987e5` (the
dark steps, not the light ones), gridlines `#2c2c2a`, and body text clears 19.4:1.

### Two anti-patterns this pass fixed

The KPI figures were breaking two documented rules and I had not noticed until re-reading the mark spec:

- **A serif display face on a hero figure** reads as decoration → hero figures are now Inter, the same
  sans as everything else.
- **`tabular-nums` on a large standalone number** makes big digits look loose → now
  `proportional-nums`; tabular is for columns that align vertically, like axis ticks.

## Layout — domain tabs

Fourteen charts in one rail was too long a list. Now five tabs — Economy (5), State (2), Society (2),
Politics (3), Limits (2) — each a 2-up grid. `span = 2` promotes a chart to a full-width row when it
needs the space: wide category labels (heatmap), a colourbar (connected scatter), or stacked panels
(small multiples). Plotly renders lazily per tab, so only the active tab's charts mount.

*Environment + Evidence merged into **Limits*** — the limits of the planet and the limits of what we
actually know. Better than two singleton tabs.

## Known gaps

- **No dark mode yet.** The token table in `R/theme.R` carries only light values. Dark is a *selected*
  set of steps validated against the dark surface, not an automatic flip — worth doing properly rather
  than inverting.
- **No table view.** The contrast WARN is currently discharged by direct labels alone; a table toggle
  would be the stronger relief.
- **No texture channel** for full-CVD / print / `forced-colors`.
