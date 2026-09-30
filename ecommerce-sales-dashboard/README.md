# E-commerce Sales Dashboard

Five questions a sales manager asks of weekly product sales, answered in a Shiny for Python dashboard
that runs in the browser (WebAssembly, no server) on [projects.karthikiyer.info](https://projects.karthikiyer.info/#sales).

**Data:** [E-commerce Demand Forecasting Dataset](https://www.kaggle.com/datasets/sergionefedov/e-commerce-demand-forecasting-dataset)
(Kaggle, CC0). 24,310 rows: 320 products × 8 categories, weekly, 4 Jul 2022 – 30 Dec 2024.
**100% synthetic**, which is why it can include the true demand hidden by stockouts.

## What it answers

| Tab | Question | Finding |
|---|---|---|
| Revenue | Where does revenue come from? | Electronics is 12.5% of products and 36% of revenue. Grocery moves 26% of units for 8% of revenue. Per product, 2024 was flat (+0.8%). |
| Seasonality | When are the peaks, what is shifting? | Every category peaks in November (toys at 1.94× a normal month) and bottoms out in July. Beauty fell 21.6% per product-week in 2024, apparel grew 9.3%. |
| Promotions | Do promos pay off? | A 25% discount needs +33% units. Only electronics (+57%) and toys (+53%) clear it; grocery loses 18.8% of revenue on promo. |
| Stockouts | What did running out cost? | $1.71M, 3.9% of revenue. Stockouts are random one-week gaps (~4.3% everywhere), so the loss follows price. |
| Product health | Which products are dying? | Last 4 weeks ÷ prior 12, seasonality removed. Below 0.6 flags a drop candidate: right 98% of the time, about 4 weeks before the product goes. |

## Traps the numbers avoid

- **Catalog size.** Products on sale swing from 4 to 301 a week, so every trend and growth figure is per product-week. Raw totals showed +7.8% growth; per product it is +0.8%.
- **Season vs promo.** Promo and regular weeks are compared within the same product and month.
- **Stockouts as fake decline.** Stockout weeks are skipped in the product-health ratio.
- **Post-Black-Friday drop.** Seasonality is removed by week of year; a monthly factor flagged 32 healthy products in late December, weekly flags 6.
- **Cheat column.** `is_declining` is a generator label a real business wouldn't have. The rule uses sales only; the label only grades it.

Revenue is not profit: there is no cost data, so a promo that grows revenue can still lose margin.

## Files

| File | What |
|---|---|
| `explore.ipynb` | Where every number was worked out, question by question |
| `app.py` | The dashboard. Reads the CSV and computes everything at start-up |
| `data/` | The Kaggle CSV and its data dictionary |

## Run it

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/shiny run app.py
```

The site build (`.github/workflows/deploy-dashboard.yml`) stages `app.py` and the CSV and runs `shinylive export` into `/sales/`.
