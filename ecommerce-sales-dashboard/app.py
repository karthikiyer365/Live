# E-commerce Sales Dashboard: five questions a sales manager asks, answered from weekly product sales.
# Runs as Shiny for Python locally (`shiny run app.py`) and as WebAssembly via shinylive on the project site.
# Every number here was worked out first in explore.ipynb; this file only presents it.
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_plotly

# Site palette (site/index.html). Pink and teal are close for red-green colorblind readers,
# so any chart that uses both also prints its values.
PINK, TEAL = "#dd0077", "#0b7c66"
INK, INK2, INK3, LINE, GRID, MID = "#1a1a1a", "#5c5c5c", "#767676", "#e0e0e0", "#ebebeb", "#f0efec"
GOOD, WARN, CRIT = "#0ca30c", "#b87d00", "#d03b3b"
FONT = "Geist, system-ui, -apple-system, sans-serif"

WATCH, DROP = 0.8, 0.6          # product-health ratio thresholds, graded in explore.ipynb
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ---------- data ----------
def load() -> pd.DataFrame:
    df = pd.read_csv(Path(__file__).parent / "data" / "ecommerce_demand_weekly.csv", parse_dates=["date"])
    df = df.sort_values(["sku", "date"]).reset_index(drop=True)
    df["year"] = df.date.dt.year
    df["ym"] = df.date.dt.to_period("M")

    # Stockouts: demand we couldn't serve, priced net of the category's return rate so it compares with `revenue`.
    df["lost_units"] = df.true_demand - df.units_sold
    return_rate = df.groupby("category").returns.sum() / df.groupby("category").units_sold.sum()
    df["lost_revenue"] = df.lost_units * df.price * (1 - df.category.map(return_rate))

    # Product health: last 4 weeks vs the 12 before, after removing the category's week-of-year pattern.
    # Stockout weeks are skipped (low sales there mean no stock, not no demand); launch weeks get no ratio.
    df["woy"] = df.date.dt.isocalendar().week.astype(int).clip(upper=52)
    woy = df.groupby(["category", "woy"]).units_sold.mean()
    df = df.join((woy / woy.groupby("category").transform("mean")).rename("season"), on=["category", "woy"])
    df["deseasoned"] = (df.units_sold / df.season).where(df.stockout == 0)
    g = df.groupby("sku").deseasoned
    recent = g.transform(lambda x: x.rolling(4, min_periods=3).mean())
    base = g.transform(lambda x: x.shift(4).rolling(12, min_periods=6).mean())
    df["ratio"] = (recent / base).where(df.is_new_launch == 0)
    return df


DF = load()
CATS = sorted(DF.category.unique())
DATES = [d.date() for d in sorted(DF.date.drop_duplicates())]  # plain dates: what the week slider sends back

# Category-level tables that never change with the filter; pages just select rows.
_m = DF.groupby(["category", "month"]).agg(units=("units_sold", "sum"), sku_weeks=("sku", "size"))
SEASON = (_m.units / _m.sku_weeks / (_m.units / _m.sku_weeks).groupby("category").transform("mean")).unstack("month")

# Year-on-year comparisons use mature weeks only: 2023 is full of low-selling launch weeks (14.7%) and
# 2024 of declining ones (10.1%), so all-week averages measure the lifecycle mix, not how products sold.
MATURE = DF[(DF.is_new_launch == 0) & (DF.is_declining == 0)]
_gm = MATURE[MATURE.year.isin([2023, 2024])].groupby(["category", "year"]).units_sold.mean().unstack()
GROWTH = _gm[2024] / _gm[2023] - 1

# Promo vs regular weeks of the same product in the same month; only product-months that had both.
PROMO_CELLS = DF.groupby(["category", "sku", "ym", "on_promo"])[["units_sold", "price", "revenue"]].mean().unstack("on_promo").dropna()

# Protect first: what one stockout week would cost each product still on sale, at its typical (deseasoned) demand
# over the last 12 weeks and its regular price. A stockout week loses about 86% of demand (explore.ipynb).
_live = DF[DF.sku.isin(DF[DF.date == DF.date.max()].sku) & (DF.date > DF.date.max() - pd.Timedelta(weeks=12))]
LIVE = _live.groupby(["sku", "category", "region"]).agg(
    weekly_units=("deseasoned", "mean"), price=("price", "max")).reset_index()  # max price = regular, not promo
_out = DF[DF.stockout == 1]
LOSS_SHARE = 1 - _out.units_sold.sum() / _out.true_demand.sum()
STOCKOUT_RATE = DF.stockout.mean()
_rr = DF.groupby("category").returns.sum() / DF.groupby("category").units_sold.sum()
LIVE["per_stockout_week"] = LIVE.weekly_units * LOSS_SHARE * LIVE.price * (1 - LIVE.category.map(_rr))
LIVE["per_year"] = LIVE.per_stockout_week * 52 * STOCKOUT_RATE


def promo_lift(cells: pd.DataFrame) -> pd.Series:
    return pd.Series({k: cells[(k, 1)].sum() / cells[(k, 0)].sum() - 1 for k in ["units_sold", "price", "revenue"]})


def label(cat: str) -> str:
    return cat.replace("_", " & ")


def money(v: float) -> str:
    return f"${v / 1e6:.2f}M" if v >= 1e6 else f"${v / 1e3:.0f}k" if v >= 1e3 else f"${v:,.0f}"


def verdict(rev_change: float) -> tuple[str, str]:
    return ("good", "Pays") if rev_change > 0.08 else ("warn", "Barely") if rev_change > 0 else ("crit", "Loses")


def take(text: str):
    return ui.p(text, class_="take")


# ---------- chart + UI helpers ----------
def style(fig: go.Figure, height: int = 340, **layout) -> go.Figure:
    fig.update_layout(template="none", height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family=FONT, color=INK2, size=12), margin=dict(l=110, r=16, t=10, b=40), showlegend=False,
                      hoverlabel=dict(bgcolor="white", bordercolor=LINE, font=dict(color=INK, family=FONT)))
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=LINE, linecolor=LINE)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=LINE, linecolor=LINE)
    fig.update_layout(**layout)
    return fig


def kpis(*items: tuple[str, str]):
    return ui.div(*[ui.div(ui.tags.b(v), ui.span(s), class_="kpi") for v, s in items], class_="kpis")


def panel(title: str, sub: str | None, *children):
    return ui.div(ui.h3(title), ui.p(sub, class_="sub") if sub else None, *children, class_="panel")


def pill(kind: str, text: str):
    return ui.span(text, class_=f"pill {kind}")


CSS = f"""
:root {{ --bs-primary: {PINK}; --bs-primary-rgb: 221, 0, 119; --bs-body-font-family: {FONT}; --pink: {PINK}; --ink: {INK}; --ink-2: {INK2}; --ink-3: {INK3}; --line: {LINE}; --line-subtle: {GRID}; }}
body {{ background: #fff; color: var(--ink); font-family: {FONT}; -webkit-font-smoothing: antialiased; }}
.container-fluid {{ max-width: 1160px; padding-inline: 32px; padding-block: 0 64px; }}
header.top {{ display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 8px 24px; padding-block: 22px 14px; }}
.eyebrow {{ font: 500 10px "Geist Mono", ui-monospace, monospace; letter-spacing: .12em; text-transform: uppercase; color: var(--pink); }}
h1 {{ font-size: 26px; font-weight: 600; letter-spacing: -.02em; margin: 4px 0 0; }}
.meta {{ font: 400 11.5px "Geist Mono", ui-monospace, monospace; color: var(--ink-3); }}
.nav-underline {{ gap: 26px; border-bottom: 1px solid var(--line-subtle); flex-wrap: nowrap; overflow-x: auto; }}
.nav-underline .nav-link {{ color: var(--ink-3); font-size: 13.5px; padding: 12px 0 10px; white-space: nowrap; }}
.nav-underline .nav-link:hover {{ color: var(--pink); }}
.nav-underline .nav-link.active {{ color: var(--pink); font-weight: 500; border-bottom-color: var(--pink); }}
.filters {{ display: flex; flex-wrap: wrap; align-items: center; gap: 4px 10px; padding-block: 14px 4px; }}
.filters .label {{ font: 500 10px "Geist Mono", ui-monospace, monospace; letter-spacing: .12em; text-transform: uppercase; color: var(--ink-3); }}
.filters .shiny-input-container {{ margin: 0; width: auto; }}
.filters .checkbox-inline {{ font-size: 12.5px; color: var(--ink-2); margin-right: 12px; }}  /* inline checkbox groups render as label.checkbox-inline > input */
.filters input[type=checkbox] {{ accent-color: var(--pink); }}
.filters input[type=checkbox]:checked {{ background-color: var(--pink); border-color: var(--pink); }}
.filters input[type=checkbox]:focus {{ box-shadow: 0 0 0 .2rem rgba(221,0,119,.2); border-color: var(--pink); }}
.page {{ display: grid; gap: 20px; padding-top: 14px; }}
.q {{ font-size: 20px; font-weight: 600; letter-spacing: -.01em; margin: 0; }}
.lede {{ color: var(--ink-2); font-size: 14.5px; line-height: 1.55; margin: 0; max-width: 68ch; }}
.kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }}
.kpi {{ border: 1px solid var(--line); border-radius: 8px; padding: 14px 16px; }}
.kpi b {{ display: block; font-size: 26px; font-weight: 600; letter-spacing: -.02em; font-variant-numeric: tabular-nums; }}
.kpi span {{ font-size: 12.5px; color: var(--ink-2); }}
.grid2 {{ display: grid; grid-template-columns: 3fr 2fr; gap: 20px; }}
.panel {{ border: 1px solid var(--line); border-radius: 8px; padding: 14px 14px 6px; min-width: 0; }}
.panel h3 {{ margin: 0 0 2px; font-size: 14px; font-weight: 600; }}
.panel .sub {{ margin: 0 0 4px; font-size: 12.5px; color: var(--ink-3); }}
.take {{ margin: 0; font-size: 15px; font-weight: 500; color: var(--ink); border-left: 3px solid var(--pink); padding: 2px 0 2px 12px; max-width: 80ch; }}
.topn {{ display: flex; align-items: center; gap: 8px; font-size: 12.5px; color: var(--ink-2); }}
.topn .shiny-input-container {{ width: 80px !important; margin: 0; }}
.note {{ font-size: 12.5px; color: var(--ink-2); border-left: 2px solid var(--line); padding-left: 10px; margin: 0; line-height: 1.5; }}
.tablewrap {{ overflow-x: auto; }}
table.t {{ width: 100%; border-collapse: collapse; font-size: 13px; font-variant-numeric: tabular-nums; }}
table.t th {{ text-align: left; font: 500 10px "Geist Mono", ui-monospace, monospace; letter-spacing: .1em; text-transform: uppercase; color: var(--ink-3); padding: 8px 10px; border-bottom: 1px solid var(--line); }}
table.t td {{ padding: 7px 10px; border-bottom: 1px solid var(--line-subtle); white-space: nowrap; }}
table.t .num {{ text-align: right; }}
.pill {{ display: inline-flex; align-items: center; gap: 5px; font-size: 12px; font-weight: 500; }}
.pill::before {{ content: ""; width: 8px; height: 8px; border-radius: 50%; background: currentColor; }}
.good {{ color: {GOOD}; }} .warn {{ color: {WARN}; }} .crit {{ color: {CRIT}; }}
.modebar-container {{ display: none; }}
.tiers {{ display: flex; gap: 18px; font-size: 13px; padding-block: 4px 10px; }}
.irs--shiny .irs-bar, .irs--shiny .irs-single, .irs--shiny .irs-handle {{ background: var(--pink); border-color: var(--pink); }}
@media (max-width: 760px) {{ .container-fluid {{ padding-inline: 16px; }} .grid2 {{ grid-template-columns: 1fr; }} }}
"""


# ---------- UI ----------
app_ui = ui.page_fluid(
    ui.head_content(
        ui.tags.title("E-commerce Sales Dashboard"),
        ui.tags.link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&display=swap"),
        ui.tags.style(CSS),
    ),
    ui.tags.header(
        ui.div(ui.div("Python · Shiny", class_="eyebrow"), ui.h1("E-commerce Sales Dashboard")),
        ui.div(f"synthetic Kaggle data · {DF.sku.nunique()} products · {DATES[0]:%d %b %Y} – {DATES[-1]:%d %b %Y} · weekly", class_="meta"),
        class_="top",
    ),
    ui.navset_underline(
        ui.nav_panel("Revenue", ui.div(
            ui.h2("Where does revenue come from?", class_="q"),
            ui.output_ui("rev_take"),
            ui.output_ui("rev_kpis"),
            ui.div(
                panel("Revenue share vs unit share", "Share of the selected categories. A long teal bar next to a short pink one means lots of boxes, little money.", output_widget("share")),
                panel("How concentrated is revenue?", "Products ranked by total revenue, cumulative share. The dot marks your top N.",
                      ui.div(ui.span("Top"), ui.input_numeric("top_n", None, 10, min=1, max=320, step=1), ui.span("products"), class_="topn"),
                      output_widget("pareto")),
                class_="grid2"),
            panel("Top products", "Products sell for 30 to 130 weeks, so a long-lived product can top the total without selling faster. Revenue per week on sale shows which ones actually sell fastest.",
                  ui.output_ui("top_table")),
            ui.p("Growth compares mature products only (no launch ramp, no decline). 2023 was full of low-selling launch weeks and 2024 of declining ones, so an all-week average would show +0.8% where the same products actually sold 1.9% less.", class_="note"),
            class_="page")),
        ui.nav_panel("Seasonality", ui.div(
            ui.h2("When are the peaks, and what is shifting?", class_="q"),
            ui.output_ui("season_take"),
            panel("Seasonal index by category and month", "1.00 = a normal month for that category. Pink = busier, teal = quieter.", output_widget("heat")),
            ui.div(
                panel("Weekly units per product, 2023 vs 2024", "Units per product per week, mature products only, by week of the year. Shows when the peak starts and whether this year ran ahead of last.", output_widget("weekly")),
                panel("Growth of mature products, 2024 vs 2023", "Units per product-week, no launch ramp, no decline.", output_widget("growth")),
                class_="grid2"),
            class_="page")),
        ui.nav_panel("Promotions", ui.div(
            ui.h2("Do promotions pay off?", class_="q"),
            ui.output_ui("promo_take"),
            ui.p("A promo takes 25% off. Revenue only grows if units rise by more than 33%. Each category compares promo weeks with regular weeks of the same product in the same month.", class_="lede"),
            ui.output_ui("promo_kpis"),
            panel("Revenue change in promo weeks", "Sorted from best to worst. The label shows how much units rose to get there.", output_widget("promo")),
            ui.p("Revenue is not profit. There is no cost data, so a promo that grows revenue can still lose margin.", class_="note"),
            class_="page")),
        ui.nav_panel("Stockouts", ui.div(
            ui.h2("What did running out of stock cost us?", class_="q"),
            ui.output_ui("so_take"),
            ui.output_ui("so_kpis"),
            ui.div(
                panel("Revenue lost by category", "Lost units × that week's price, net of the category's return rate.", output_widget("lost")),
                panel("Cost of one stockout week, per product on sale", "One dot per product still on sale. Stockouts hit every product at about the same rate, so the cost is set by price and demand.", output_widget("so_cost")),
                class_="grid2"),
            panel("Protect first", "Products still on sale, ranked by what one stockout week would cost: typical weekly demand (seasonality removed) × 86% lost × regular price, net of returns. Per year assumes the usual 4.3% of weeks out of stock.",
                  ui.output_ui("so_table")),
            class_="page")),
        ui.nav_panel("Product health", ui.div(
            ui.h2("Which products are dying?", class_="q"),
            ui.output_ui("health_take"),
            ui.p(f"Sales in the last 4 weeks divided by the 12 weeks before, after removing the seasonal pattern and skipping stockout weeks. "
                 f"Below {WATCH} goes on watch. Below {DROP} is a drop candidate.", class_="lede"),
            panel("As of week", "Move back in time to see what the list would have said then.",
                  ui.input_slider("week", None, min=DATES[16], max=DATES[-1], value=DATES[-1], step=7, time_format="%d %b %Y", width="100%"),
                  ui.output_ui("tiers")),
            ui.div(
                panel("Flagged products", "Select a row to see its trend.", ui.output_data_frame("health_table")),
                panel("Trend", "Top: units with seasonality removed. Bottom: the ratio, with watch and drop lines.",
                      ui.output_ui("sku_title"), output_widget("sku_trend")),
                class_="grid2"),
            ui.p("How reliable is this? The dataset has a hidden label marking each product's final decline. Graded against it, drop flags were right 97% of the time "
                 "in 2023 and 98% in 2024, and all 163 retired products were flagged, typically 7 weeks into an 11-week decline, about 4 weeks before they left. "
                 "Most false alarms fall in July, October and November, where the seasonal swing is steepest. Check a drop flag before acting.", class_="note"),
            class_="page")),
        id="tab",
        header=ui.div(ui.span("Category", class_="label"),
                      ui.input_checkbox_group("cats", None, {c: label(c) for c in CATS}, selected=CATS, inline=True),
                      class_="filters"),
    ),
)


# ---------- server ----------
def server(input, output, session):
    @reactive.calc
    def cats() -> list[str]:
        return list(input.cats()) or CATS  # nothing ticked = everything

    @reactive.calc
    def df() -> pd.DataFrame:
        return DF[DF.category.isin(cats())]

    # Revenue
    @reactive.calc
    def sku_rev() -> pd.DataFrame:
        s = df().groupby(["sku", "category"]).agg(revenue=("revenue", "sum"), weeks=("date", "size")).reset_index()
        s["per_week"] = s.revenue / s.weeks
        return s.sort_values("revenue", ascending=False, ignore_index=True)

    @reactive.calc
    def top_n() -> int:
        return max(1, min(int(input.top_n() or 10), len(sku_rev())))

    @render.ui
    def rev_take():
        c = df().groupby("category").agg(revenue=("revenue", "sum"), units=("net_units", "sum"))
        c = c / c.sum()
        big, vol = c.revenue.idxmax(), c.units.idxmax()
        if big == vol:
            return take(f"{label(big).capitalize()} leads on both money and volume: {c.revenue[big]:.0%} of revenue, {c.units[big]:.0%} of units.")
        return take(f"{label(big).capitalize()} makes the money ({c.revenue[big]:.0%} of revenue from {c.units[big]:.0%} of units). "
                    f"{label(vol).capitalize()} moves the most boxes ({c.units[vol]:.0%} of units) for {c.revenue[vol]:.0%} of revenue.")

    @render.ui
    def rev_kpis():
        per = MATURE[MATURE.category.isin(cats()) & MATURE.year.isin([2023, 2024])].groupby("year").agg(rev=("revenue", "sum"), n=("sku", "size"))
        per = per.rev / per.n
        s = sku_rev()
        n80 = int((s.revenue.cumsum() < 0.8 * s.revenue.sum()).sum()) + 1
        return kpis((money(s.revenue.sum()), "revenue, net of returns"), (str(len(s)), "products"),
                    (f"{per[2024] / per[2023] - 1:+.1%}", "revenue per mature product-week, 2024 vs 2023"),
                    (f"{n80} of {len(s)}", "products make 80% of revenue"))

    @render_plotly
    def share():
        c = df().groupby("category").agg(revenue=("revenue", "sum"), units=("net_units", "sum"))
        c = (c / c.sum()).sort_values("revenue")
        y = [label(i) for i in c.index]
        fig = go.Figure([
            go.Bar(name="unit share", y=y, x=c.units, orientation="h", marker=dict(color=TEAL, cornerradius=4),
                   text=[f"{v:.0%}" for v in c.units], textposition="outside", cliponaxis=False, hovertemplate="%{y}<br>unit share %{x:.1%}<extra></extra>"),
            go.Bar(name="revenue share", y=y, x=c.revenue, orientation="h", marker=dict(color=PINK, cornerradius=4),
                   text=[f"{v:.0%}" for v in c.revenue], textposition="outside", cliponaxis=False, hovertemplate="%{y}<br>revenue share %{x:.1%}<extra></extra>"),
        ])
        return style(fig, height=380, barmode="group", bargap=0.25, bargroupgap=0.08, showlegend=True,
                     legend=dict(orientation="h", y=1.08, x=0, traceorder="reversed"), margin=dict(l=110, r=40, t=30, b=36),
                     xaxis=dict(tickformat=".0%"))

    @render_plotly
    def pareto():
        s, n = sku_rev(), top_n()
        cum = s.revenue.cumsum() / s.revenue.sum()
        n80 = int((cum < 0.8).sum()) + 1
        x = cum.index + 1
        fig = go.Figure([
            go.Scatter(x=x, y=cum, mode="lines", line=dict(color=INK3, width=2), hovertemplate="top %{x} products<br>%{y:.1%} of revenue<extra></extra>"),
            go.Scatter(x=x[:n], y=cum[:n], mode="lines", line=dict(color=PINK, width=3), hoverinfo="skip"),  # the top N, drawn over the curve
            go.Scatter(x=[n], y=[cum[n - 1]], mode="markers", marker=dict(size=10, color=PINK, line=dict(color="white", width=2)), hoverinfo="skip"),
        ])
        fig.add_hline(y=0.8, line=dict(dash="dot", color=INK3, width=1))
        fig.add_annotation(x=n, y=cum[n - 1], text=f"top {n} → {cum[n - 1]:.0%} of revenue", showarrow=False, xanchor="left", xshift=10, yshift=10, font=dict(color=INK))
        fig.add_annotation(x=n80, y=0.8, text=f"{n80} products → 80%", showarrow=False, xanchor="left", xshift=8, yshift=-12, font=dict(color=INK3, size=11))
        return style(fig, height=350, margin=dict(l=50, r=16, t=10, b=40), xaxis=dict(title="products, ranked"), yaxis=dict(tickformat=".0%", range=[0, 1.02]))

    @render.ui
    def top_table():
        s, total = sku_rev().head(top_n()), sku_rev().revenue.sum()
        head = ui.tags.tr(*[ui.tags.th(h, class_=None if h in ("Product", "Category") else "num")
                            for h in ["#", "Product", "Category", "Revenue", "Share", "Weeks on sale", "Revenue / week"]])
        rows = [ui.tags.tr(ui.tags.td(i + 1, class_="num"), ui.tags.td(r.sku), ui.tags.td(label(r.category)), ui.tags.td(money(r.revenue), class_="num"),
                           ui.tags.td(f"{r.revenue / total:.1%}", class_="num"), ui.tags.td(r.weeks, class_="num"), ui.tags.td(money(r.per_week), class_="num"))
                for i, r in s.iterrows()]
        return ui.div(ui.tags.table(head, *rows, class_="t"), class_="tablewrap", style="max-height:420px;overflow-y:auto")

    # Seasonality
    @render_plotly
    def heat():
        s = SEASON.loc[cats()]
        s = s.loc[s.max(axis=1).sort_values().index]
        fig = go.Figure(go.Heatmap(z=s.values, x=MONTHS, y=[label(c) for c in s.index], zmin=0.6, zmax=2.0,
                                   colorscale=[[0, TEAL], [(1 - 0.6) / 1.4, MID], [1, PINK]], xgap=2, ygap=2,
                                   texttemplate="%{z:.2f}", textfont=dict(size=11, color=INK), colorbar=dict(thickness=10, outlinewidth=0),
                                   hovertemplate="%{y} · %{x}<br>%{z:.2f}× a normal month<extra></extra>"))
        return style(fig, height=max(200, 44 * len(s) + 50), margin=dict(l=110, r=10, t=10, b=30),
                     xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))

    @render.ui
    def season_take():
        s, g = SEASON.loc[cats()], GROWTH.loc[cats()]
        peak = s.max(axis=0).idxmax()
        swing = s.max(axis=1).idxmax()
        msg = (f"{MONTHS[peak - 1]} is the peak for every selected category; {label(swing)} swings hardest "
               f"({s.loc[swing].max():.2f}× a normal month), so its stock needs to land by {MONTHS[peak - 2]}.")
        if len(g) > 1:
            msg += f" Mature products: {label(g.idxmax())} changed {g.max():+.1%}, {label(g.idxmin())} {g.min():+.1%}."
        return take(msg)

    @render_plotly
    def weekly():
        m = MATURE[MATURE.category.isin(cats())]
        iso = m.date.dt.isocalendar()  # ISO year, so 30 Dec 2024 (week 1 of 2025) doesn't land on top of Jan 2024
        w = m.groupby([iso.year.rename("y"), iso.week.rename("wk")]).units_sold.mean().unstack("y")
        fig = go.Figure()
        for y, color in [(2023, TEAL), (2024, PINK)]:
            s = w[y].dropna()
            fig.add_trace(go.Scatter(x=s.index, y=s, mode="lines", name=str(y), line=dict(color=color, width=2),
                                     hovertemplate=f"{y} · week %{{x}}<br>%{{y:.1f}} units per product<extra></extra>"))
            fig.add_annotation(x=s.index[0], y=s.iloc[0], text=str(y), showarrow=False, xanchor="right", xshift=-6, font=dict(color=color, size=12))  # lines are apart in week 1, together at the peak
        return style(fig, height=380, margin=dict(l=84, r=16, t=30, b=40), hovermode="x unified", showlegend=True,
                     legend=dict(orientation="h", y=1.1, x=0), xaxis=dict(title="week of the year", range=[1, 53]))

    @render_plotly
    def growth():
        g = GROWTH.loc[cats()].sort_values()
        fig = go.Figure(go.Bar(y=[label(c) for c in g.index], x=g, orientation="h",
                               marker=dict(color=[PINK if v >= 0 else TEAL for v in g], cornerradius=4),
                               text=[f"{v:+.1%}" for v in g], textposition="outside", cliponaxis=False,
                               hovertemplate="%{y}: %{x:+.1%}<extra></extra>"))
        pad = max(abs(g.min()), abs(g.max())) * 0.45  # room for the outside labels on both sides of zero
        return style(fig, height=380, margin=dict(l=110, r=16, t=10, b=30), xaxis=dict(tickformat="+.0%", range=[min(g.min(), 0) - pad, max(g.max(), 0) + pad]))

    # Promotions
    @reactive.calc
    def promo_cells() -> pd.DataFrame:
        return PROMO_CELLS[PROMO_CELLS.index.get_level_values("category").isin(cats())]

    @reactive.calc
    def promo_rows() -> pd.DataFrame:
        return promo_cells().groupby(level="category").apply(promo_lift).sort_values("revenue")

    @render.ui
    def promo_take():
        r = promo_rows()
        win, lose = r[r.revenue > 0].index[::-1], r[r.revenue <= 0].index
        parts = []
        if len(lose):
            parts.append("Stop promos in " + ", ".join(f"{label(c)} ({r.revenue[c]:+.1%})" for c in lose[:2]) + ".")
        if len(win):
            parts.append("Keep them in " + " and ".join(label(c) for c in win[:2]) + ".")
        return take(" ".join(parts))

    @render.ui
    def promo_kpis():
        cells, r = promo_cells(), promo_rows()
        a = promo_lift(cells)
        pays = sum(verdict(v)[1] == "Pays" for v in r.revenue)
        return kpis((f"{pays} of {len(r)}", "categories where promos clearly pay"), (f"{a.units_sold:+.1%}", "units in promo weeks"),
                    (f"{a.price:.0%}", "price in promo weeks"), (f"{len(cells):,}", "product-months compared"))

    @render_plotly
    def promo():
        r = promo_rows()
        colors = {"good": GOOD, "warn": WARN, "crit": CRIT}
        fig = go.Figure(go.Bar(
            y=[label(c) for c in r.index], x=r.revenue, orientation="h",
            marker=dict(color=[colors[verdict(v)[0]] for v in r.revenue], cornerradius=4),
            text=[f"{verdict(v)[1]} · {v:+.1%} revenue · units {u:+.0%}" for v, u in zip(r.revenue, r.units_sold)],
            textposition="outside", cliponaxis=False, textfont=dict(color=INK2),
            hovertemplate="%{y}<br>revenue %{x:+.1%}<extra></extra>"))
        pad = max(abs(r.revenue.min()), abs(r.revenue.max())) * 1.3  # labels are long; leave room on both sides
        return style(fig, height=max(220, 40 * len(r) + 60), margin=dict(l=110, r=16, t=10, b=30),
                     xaxis=dict(tickformat="+.0%", zeroline=True, zerolinecolor=INK3, range=[min(r.revenue.min(), 0) - pad, max(r.revenue.max(), 0) + pad]))

    # Stockouts
    @reactive.calc
    def live() -> pd.DataFrame:
        return LIVE[LIVE.category.isin(cats())].sort_values("per_stockout_week", ascending=False, ignore_index=True)

    @render.ui
    def so_take():
        top = live().head(10)
        if top.empty:
            return None
        lead = top.category.value_counts()
        return take(f"Protect {label(lead.index[0])} first: {lead.iloc[0]} of the 10 costliest products to run out of are {label(lead.index[0])}. "
                    f"One stockout week of {top.sku[0]} costs about {money(top.per_stockout_week[0])}.")

    @render.ui
    def so_kpis():
        d = df()
        out = d[d.stockout == 1]
        return kpis((money(d.lost_revenue.sum()), "revenue lost to stockouts"), (f"{d.lost_revenue.sum() / d.revenue.sum():.1%}", "of revenue"),
                    (f"{len(out):,}", f"stockout weeks ({d.stockout.mean():.1%} of all)"),
                    (f"{1 - out.units_sold.sum() / out.true_demand.sum():.0%}", "of demand lost in a stockout week"))

    @render_plotly
    def lost():
        c = df().groupby("category").lost_revenue.sum().sort_values()
        fig = go.Figure(go.Bar(y=[label(i) for i in c.index], x=c, orientation="h", marker=dict(color=PINK, cornerradius=4),
                               text=[money(v) for v in c], textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x:$,.0f}<extra></extra>"))
        return style(fig, margin=dict(l=110, r=56, t=10, b=30), xaxis=dict(tickprefix="$", tickformat="~s"))

    @render_plotly
    def so_cost():
        v = live()
        order = v.groupby("category").per_stockout_week.median().sort_values().index
        fig = go.Figure(go.Box(
            y=v.category.map(label), x=v.per_stockout_week, orientation="h", boxpoints="all", jitter=0.5, pointpos=0,
            fillcolor="rgba(0,0,0,0)", line=dict(color="rgba(0,0,0,0)"), marker=dict(color=PINK, size=7, opacity=0.75, line=dict(color="white", width=1)),
            text=v.sku, hovertemplate="%{text}<br>%{x:$,.0f} per stockout week<extra></extra>"))
        return style(fig, margin=dict(l=110, r=16, t=10, b=40), yaxis=dict(categoryorder="array", categoryarray=[label(c) for c in order]),
                     xaxis=dict(tickprefix="$", tickformat="~s", title="revenue lost in one stockout week"))

    @render.ui
    def so_table():
        top = live().head(10)
        head = ui.tags.tr(*[ui.tags.th(h, class_=None if h in ("Product", "Category", "Home region") else "num")
                            for h in ["#", "Product", "Category", "Home region", "Typical units / week", "Price", "Lost per stockout week", "Expected per year"]])
        rows = [ui.tags.tr(ui.tags.td(i + 1, class_="num"), ui.tags.td(r.sku), ui.tags.td(label(r.category)), ui.tags.td(r.region),
                           ui.tags.td(f"{r.weekly_units:.0f}", class_="num"), ui.tags.td(f"${r.price:,.0f}", class_="num"),
                           ui.tags.td(money(r.per_stockout_week), class_="num"), ui.tags.td(money(r.per_year), class_="num"))
                for i, r in top.iterrows()]
        return ui.div(ui.tags.table(head, *rows, class_="t"), class_="tablewrap")

    # Product health
    @reactive.calc
    def week_rows() -> pd.DataFrame:
        d = df()
        w = d[(d.date == pd.Timestamp(input.week())) & d.ratio.notna()].copy()
        w["flag"] = pd.cut(w.ratio, [0, DROP, WATCH, float("inf")], labels=["drop", "watch", "keep"], right=False)
        return w

    @reactive.calc
    def flagged() -> pd.DataFrame:
        w = week_rows()
        f = w[w.flag != "keep"].sort_values("ratio")
        return pd.DataFrame({"Product": f.sku, "Category": f.category.map(label), "Home region": f.region,
                             "Ratio": f.ratio.round(2), "Flag": f.flag.astype(str)})

    @render.ui
    def health_take():
        n = week_rows().flag.value_counts()
        drop = flagged()[lambda f: f.Flag == "drop"].Product.tolist()
        if not drop:
            return take(f"No drop candidates as of {input.week():%d %b %Y}. {n.get('watch', 0)} products on watch.")
        return take(f"{len(drop)} drop candidate{'s' if len(drop) > 1 else ''} as of {input.week():%d %b %Y}: {', '.join(drop[:5])}"
                    f"{' …' if len(drop) > 5 else ''}. Start clearing stock; {n.get('watch', 0)} more on watch.")

    @render.ui
    def tiers():
        n = week_rows().flag.value_counts()
        return ui.div(pill("good", f"{n.get('keep', 0)} keep"), pill("warn", f"{n.get('watch', 0)} watch"), pill("crit", f"{n.get('drop', 0)} drop"), class_="tiers")

    @render.data_frame
    def health_table():
        return render.DataGrid(flagged(), selection_mode="row", height="400px", width="100%")

    @reactive.calc
    def picked() -> str | None:
        f = flagged()
        if f.empty:
            return None
        rows = health_table.cell_selection()["rows"]
        return f.iloc[rows[0]].Product if rows and rows[0] < len(f) else f.iloc[0].Product

    @render.ui
    def sku_title():
        k = picked()
        if k is None:
            return ui.p("No products flagged this week.", class_="sub")
        r = DF[DF.sku == k].iloc[0]
        return ui.p(ui.tags.b(k), f" · {label(r.category)} · {r.region}", style="margin:0;font-size:13px")

    @render_plotly
    def sku_trend():
        k = picked()
        h = DF[DF.sku == k] if k else DF.iloc[0:0]
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.62, 0.38], vertical_spacing=0.08)
        fig.add_trace(go.Scatter(x=h.date, y=h.deseasoned, mode="lines", line=dict(color=PINK, width=2), connectgaps=False,
                                 hovertemplate="%{x|%d %b %Y}<br>%{y:.1f} units, seasonality removed<extra></extra>"), row=1, col=1)
        fig.add_trace(go.Scatter(x=h.date, y=h.ratio, mode="lines", line=dict(color=INK2, width=2),
                                 hovertemplate="%{x|%d %b %Y}<br>ratio %{y:.2f}<extra></extra>"), row=2, col=1)
        fig.add_hline(y=WATCH, line=dict(dash="dot", color=WARN, width=1), row=2, col=1)
        fig.add_hline(y=DROP, line=dict(dash="dot", color=CRIT, width=1), row=2, col=1)
        fig.add_vline(x=pd.Timestamp(input.week()), line=dict(color=PINK, width=1))
        return style(fig, height=380, margin=dict(l=44, r=10, t=10, b=30), yaxis2=dict(range=[0, 1.6]))


app = App(app_ui, server)
