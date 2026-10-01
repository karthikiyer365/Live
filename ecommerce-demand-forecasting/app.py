# Promo planner: a PM picks a product or category, a horizon and an optional promo, and sees the demand forecast with its p90.
# Every number comes from data/forecasts.csv, written by demand_forecasting.ipynb. Promo effects don't carry over between
# weeks, so each week was forecast twice (promo off / on) and this app just picks one per week. No model runs here.
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_plotly

HERE = Path(__file__).parent
PINK, TEAL = "#dd0077", "#0b7c66"  # site palette (site/index.html)
INK, INK2, INK3, LINE, GRID = "#1a1a1a", "#5c5c5c", "#767676", "#e0e0e0", "#ebebeb"
FONT = "Geist, system-ui, -apple-system, sans-serif"
DISCOUNT = 0.25     # the only promo depth in the data, so the only one the model can price
HISTORY_WEEKS = 26

FC = pd.read_csv(HERE / "data" / "forecasts.csv", parse_dates=["week"])
_hist = pd.read_csv(HERE / "data" / "ecommerce_demand_weekly.csv", parse_dates=["date"], usecols=["sku", "date", "true_demand"])
HIST = _hist[_hist.date > _hist.date.max() - pd.Timedelta(weeks=HISTORY_WEEKS)]
PRODUCTS = FC.drop_duplicates("sku").sort_values(["category", "sku"])
CATS = sorted(PRODUCTS.category.unique())
HORIZONS = {"4 weeks": 4, "3 months": 13}


def label(cat: str) -> str:
    return cat.replace("_", " & ")


def units(v: float) -> str:
    return f"{v:,.0f}"


CSS = f"""
:root {{ --bs-primary: {PINK}; --bs-primary-rgb: 221, 0, 119; --bs-body-font-family: {FONT}; }}
body {{ background: #fff; color: {INK}; font-family: {FONT}; -webkit-font-smoothing: antialiased; }}
.container-fluid {{ max-width: 1160px; padding-inline: 32px; padding-block: 0 64px; }}
header.top {{ display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 8px 24px; padding-block: 22px 18px; border-bottom: 1px solid {GRID}; margin-bottom: 20px; }}
.eyebrow {{ font: 500 10px "Geist Mono", ui-monospace, monospace; letter-spacing: .12em; text-transform: uppercase; color: {PINK}; }}
h1 {{ font-size: 26px; font-weight: 600; letter-spacing: -.02em; margin: 4px 0 0; }}
.meta {{ font: 400 11.5px "Geist Mono", ui-monospace, monospace; color: {INK3}; }}
.layout {{ display: grid; grid-template-columns: 300px 1fr; gap: 24px; align-items: start; }}
.controls {{ border: 1px solid {LINE}; border-radius: 8px; padding: 16px; display: grid; gap: 4px; }}
.controls h3 {{ font: 500 10px "Geist Mono", ui-monospace, monospace; letter-spacing: .12em; text-transform: uppercase; color: {INK3}; margin: 10px 0 2px; }}
.controls h3:first-child {{ margin-top: 0; }}
.controls .form-label, .controls label {{ font-size: 13px; color: {INK2}; }}
.controls .hint {{ font-size: 12px; color: {INK3}; margin: -4px 0 6px; line-height: 1.45; }}
.controls .shiny-input-container {{ width: 100% !important; }}
.controls .form-check-input:checked, .controls input[type=radio]:checked {{ background-color: {PINK}; border-color: {PINK}; }}  /* inline radios render as bare inputs */
.controls input[type=radio] {{ accent-color: {PINK}; }}
.controls .form-check-input:focus {{ box-shadow: 0 0 0 .2rem rgba(221,0,119,.2); border-color: {PINK}; }}
.irs--shiny .irs-bar, .irs--shiny .irs-single, .irs--shiny .irs-handle {{ background: {PINK}; border-color: {PINK}; }}
.results {{ display: grid; gap: 16px; min-width: 0; }}
.take {{ margin: 0; font-size: 15px; font-weight: 500; border-left: 3px solid {PINK}; padding: 2px 0 2px 12px; }}
.kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; }}
.kpi {{ border: 1px solid {LINE}; border-radius: 8px; padding: 12px 14px; }}
.kpi b {{ display: block; font-size: 24px; font-weight: 600; letter-spacing: -.02em; font-variant-numeric: tabular-nums; }}
.kpi span {{ font-size: 12.5px; color: {INK2}; }}
.panel {{ border: 1px solid {LINE}; border-radius: 8px; padding: 14px 14px 6px; min-width: 0; }}
.panel h4 {{ margin: 0 0 2px; font-size: 14px; font-weight: 600; }}
.panel .sub {{ margin: 0 0 4px; font-size: 12.5px; color: {INK3}; }}
.note {{ font-size: 12.5px; color: {INK2}; border-left: 2px solid {LINE}; padding-left: 10px; margin: 0; line-height: 1.5; }}
table.t {{ width: 100%; border-collapse: collapse; font-size: 13px; font-variant-numeric: tabular-nums; }}
table.t th {{ text-align: right; font: 500 10px "Geist Mono", ui-monospace, monospace; letter-spacing: .1em; text-transform: uppercase; color: {INK3}; padding: 8px 10px; border-bottom: 1px solid {LINE}; }}
table.t td {{ text-align: right; padding: 7px 10px; border-bottom: 1px solid {GRID}; }}
table.t th:first-child, table.t td:first-child {{ text-align: left; }}
table.t tr.promo td {{ background: #fdf2f8; }}
.modebar-container {{ display: none; }}
@media (max-width: 760px) {{ .container-fluid {{ padding-inline: 16px; }} .layout {{ grid-template-columns: 1fr; }} }}
"""

app_ui = ui.page_fluid(
    ui.head_content(
        ui.tags.title("Promo Planner"),
        ui.tags.link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&display=swap"),
        ui.tags.style(CSS),
    ),
    ui.tags.header(
        ui.div(ui.div("ML · Forecasting", class_="eyebrow"), ui.h1("Promo Planner")),
        ui.div(f"forecast from {FC.week.min() - pd.Timedelta(weeks=1):%d %b %Y} · {PRODUCTS.shape[0]} products on sale · synthetic data", class_="meta"),
        class_="top",
    ),
    ui.div(
        ui.div(
            ui.h3("What to forecast"),
            ui.input_radio_buttons("scope", None, {"product": "One product", "category": "A whole category"}, selected="product", inline=True),
            ui.panel_conditional("input.scope === 'product'",
                                 ui.input_select("sku", "Product", {label(c): {s: s for s in PRODUCTS[PRODUCTS.category == c].sku} for c in CATS},
                                                 selected="ELE-1031")),
            ui.panel_conditional("input.scope === 'category'", ui.input_select("cat", "Category", {c: label(c) for c in CATS})),
            ui.h3("How far ahead"),
            ui.input_radio_buttons("horizon", None, list(HORIZONS), selected="4 weeks", inline=True),
            ui.p("Separate models: the 3-month one is less sure the further out it goes.", class_="hint"),
            ui.h3("Promotion"),
            ui.input_switch("promo", f"Run a {DISCOUNT:.0%}-off promo", False),
            ui.panel_conditional("input.promo",
                                 ui.output_ui("start_ui"),
                                 ui.input_slider("weeks", "Length (weeks)", min=1, max=4, value=1, step=1),
                                 ui.p(f"{DISCOUNT:.0%} off is the only discount in the history, so it's the only one the model can price.", class_="hint")),
            class_="controls"),
        ui.div(
            ui.output_ui("take"),
            ui.output_ui("kpis"),
            ui.div(ui.h4("Weekly demand"), ui.p("Last 26 weeks, then the forecast. The band runs up to p90; shaded weeks are on promo.", class_="sub"),
                   output_widget("chart"), class_="panel"),
            ui.div(ui.h4("Week by week"), ui.output_ui("table"), class_="panel"),
            ui.p("p90 is the level to stock to cover about 9 weeks in 10 (in backtests it covered 87–88%). For a category it is the sum of each "
                 "product's p90, which is on the safe side. Revenue is at regular price outside promo weeks and 25% off inside them.", class_="note"),
            class_="results"),
        class_="layout"),
)


def server(input, output, session):
    @reactive.calc
    def skus() -> list[str]:
        return [input.sku()] if input.scope() == "product" else PRODUCTS[PRODUCTS.category == input.cat()].sku.tolist()

    @reactive.calc
    def weeks() -> pd.DatetimeIndex:
        return pd.DatetimeIndex(sorted(FC[FC.horizon == input.horizon()].week.unique()))

    @render.ui
    def start_ui():
        w = weeks()
        choices = {str(d.date()): f"{d:%d %b %Y}" for d in w}
        with reactive.isolate():  # keep the PM's start week when the horizon changes, if that week still exists
            current = input.start() if "start" in input else None  # not created yet on the first render
        return ui.input_select("start", "Starts the week of", choices, selected=current if current in choices else str(w[0].date()))

    @reactive.calc
    def promo_weeks() -> set:
        if not input.promo() or input.start() is None:
            return set()
        w = list(weeks())
        start = w.index(pd.Timestamp(input.start())) if pd.Timestamp(input.start()) in w else 0
        return set(w[start: start + input.weeks()])  # a promo running past the horizon is cut at its end

    @reactive.calc
    def plan() -> pd.DataFrame:
        f = FC[(FC.horizon == input.horizon()) & FC.sku.isin(skus())]
        on = f.week.isin(promo_weeks())
        chosen = f[((f.promo == 1) & on) | ((f.promo == 0) & ~on)]  # promo-on rows for promo weeks, promo-off rows otherwise
        base = f[f.promo == 0]
        price = chosen.price * chosen.promo.map({0: 1.0, 1: 1 - DISCOUNT})
        weekly = chosen.assign(revenue=chosen.forecast * price).groupby("week").agg(forecast=("forecast", "sum"), p90=("p90", "sum"), revenue=("revenue", "sum"))
        weekly["no_promo"] = base.groupby("week").forecast.sum()
        weekly["promo"] = weekly.index.isin(promo_weeks())
        return weekly

    def who() -> str:
        return input.sku() if input.scope() == "product" else f"all {len(skus())} {label(input.cat())} products"

    @render.ui
    def take():
        p = plan()
        msg = f"{who()}: about {units(p.forecast.sum())} units over the next {input.horizon()}. Stock up to {units(p.p90.sum())} to cover most weeks."
        if p.promo.any():
            gain = p.forecast.sum() / p.no_promo.sum() - 1
            msg += f" The {p.promo.sum()}-week promo adds {units(p.forecast.sum() - p.no_promo.sum())} units ({gain:+.0%})."
        return ui.p(msg, class_="take")

    @render.ui
    def kpis():
        p = plan()
        items = [(units(p.forecast.sum()), f"units forecast, next {input.horizon()}"), (units(p.p90.sum()), "p90: stock to cover most weeks"),
                 (f"${p.revenue.sum():,.0f}", "forecast revenue"),
                 (f"{p.forecast.sum() / p.no_promo.sum() - 1:+.0%}" if p.promo.any() else "—", "change from the promo")]
        return ui.div(*[ui.div(ui.tags.b(v), ui.span(s), class_="kpi") for v, s in items], class_="kpis")

    @render_plotly
    def chart():
        p = plan()
        h = HIST[HIST.sku.isin(skus())].groupby("date").true_demand.sum()
        fig = go.Figure()
        for wk in p.index[p.promo]:
            fig.add_vrect(x0=wk - pd.Timedelta(days=3.5), x1=wk + pd.Timedelta(days=3.5), fillcolor=PINK, opacity=0.08, line_width=0)
        fig.add_trace(go.Scatter(x=h.index, y=h.values, mode="lines", name="demand (history)", line=dict(color=INK3, width=2),
                                 hovertemplate="%{x|%d %b %Y}<br>%{y:,.0f} units<extra></extra>"))
        fig.add_trace(go.Scatter(x=p.index, y=p.p90, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=p.index, y=p.forecast, mode="lines+markers", name="forecast", line=dict(color=PINK, width=2.5),
                                 fill="tonexty", fillcolor="rgba(221,0,119,0.12)", marker=dict(size=6),
                                 customdata=p.p90, hovertemplate="%{x|%d %b %Y}<br>forecast %{y:,.0f} · p90 %{customdata:,.0f}<extra></extra>"))
        if p.promo.any():
            fig.add_trace(go.Scatter(x=p.index, y=p.no_promo, mode="lines", name="without the promo", line=dict(color=TEAL, width=1.5, dash="dot"),
                                     hovertemplate="%{x|%d %b %Y}<br>%{y:,.0f} units without the promo<extra></extra>"))
        fig.update_layout(template="none", height=360, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(family=FONT, color=INK2, size=12), margin=dict(l=50, r=16, t=30, b=36), hovermode="x unified",
                          legend=dict(orientation="h", y=1.1, x=0), hoverlabel=dict(bgcolor="white", bordercolor=LINE, font=dict(color=INK, family=FONT)))
        fig.update_xaxes(gridcolor=GRID, linecolor=LINE)
        fig.update_yaxes(gridcolor=GRID, linecolor=LINE, rangemode="tozero", title="units per week")
        return fig

    @render.ui
    def table():
        p = plan()
        head = ui.tags.tr(*[ui.tags.th(h) for h in ["Week of", "Promo", "Forecast", "p90", "Without promo", "Revenue"]])
        rows = [ui.tags.tr(ui.tags.td(f"{w:%d %b %Y}"), ui.tags.td("25% off" if r.promo else "—"), ui.tags.td(units(r.forecast)),
                           ui.tags.td(units(r.p90)), ui.tags.td(units(r.no_promo)), ui.tags.td(f"${r.revenue:,.0f}"),
                           class_="promo" if r.promo else None) for w, r in p.iterrows()]
        return ui.div(ui.tags.table(head, *rows, class_="t"), style="overflow-x:auto")


app = App(app_ui, server)
