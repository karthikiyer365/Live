# E-commerce Demand Forecasting

Forecast weekly demand per product **4 weeks** and **3 months** ahead, with a **p90** stocking range, and let a PM test a promo
before running it. Two pages on [projects.karthikiyer.info](https://projects.karthikiyer.info/#forecast): the method notebook and
the [promo planner](https://projects.karthikiyer.info/#forecast-app).

**Data:** [E-commerce Demand Forecasting Dataset](https://www.kaggle.com/datasets/sergionefedov/e-commerce-demand-forecasting-dataset)
(Kaggle, CC0), 320 products × 131 weekly rows, Jul 2022 – Dec 2024. **100% synthetic**, which is why it includes the true demand hidden by stockouts.

## Key ideas

> **1 · No cheating.** A forecast may only use what is known on forecast day. Every column is classified before modelling; future-week
> sales, returns, stockouts and the dataset's hidden labels (`seasonal_index`, `is_declining`) are banned. *(notebook Step 3)*

> **2 · Fill stockout weeks.** A stockout week records only what was on the shelf (14% of real demand), not what customers wanted. A business
> knows when it was out of stock, so each stockout week is replaced with the average of the product's last 2 in-stock weeks. That stops the
> model learning that demand collapsed. *(Step 11)*

> **3 · What the model sees, built as of the forecast date.** Recent selling levels (4 / 12 / 26 weeks), level with seasonality removed, trend
> (last 4 ÷ last 12 weeks), the category's seasonal factor for the target week, same week last year, weeks since launch, category, regular price,
> weeks ahead, and the planned promo. **Proof of no cheating:** scrambling every week after the forecast date changes none of the 3,380 feature
> rows tested. *(Step 12)*

> **4 · Models compared on equal terms.** HistGradientBoosting (Poisson for the forecast, quantile 0.9 for p90), one pair per horizon, trained
> three ways (raw / stockouts filled / perfect history) and scored against three simple rules (last 4 weeks, level × season, same week last
> year) with **WAPE** (share of units missed) and **bias** (over/under), against true demand, on the same rolling folds. *(Steps 13–16, 19)*

> **5 · Dying products are over-forecast by +38% (4 weeks) and +73% (3 months).** Nothing in their history warns of the decline, and the small
> overall bias hides it because healthy products run under (−5%). In a warehouse that means dead stock, so the planner warns when sales are
> already slowing. *(Steps 17, 20)*

> **6 · Plan to the p90 of the total.** Adding weekly p90s covers 94–97% of horizon totals instead of 90%. *(Step 22)*

> **7 · Promo forecasts are precomputed, and that is exact.** A promo's lift doesn't carry into the next week, so forecasting each week with the
> promo off and on covers every plan a PM can enter. *(Step 23)*

## Results (rolling backtests, scored against true demand)

| | 4 weeks | 3 months |
|---|---|---|
| Model error, weekly (WAPE) | **15.6%** | **19.7%** |
| Best simple rule | 21.6% (last 4 weeks) | 23.8% (level × season) |
| Error cut | −28% | −17% |
| Error on the horizon total | 11.7% | 14.2% |
| Error weighted by revenue | 16.7% | 20.6% |
| Error in Nov–Dec weeks | 14.4% | 24.3% |
| Bias: launch / mature · final decline | −4.6% · +38% | −6.5% · +73% |
| Weekly p90 covers | 87% of weeks | 88% of weeks |
| p90 of the total covers (one product, out of fold) | 89.5% | 87.8% |

| Training target (4-week model) | WAPE | Bias |
|---|---|---|
| A · raw units sold | 18.7% | −6.3% |
| **B · stockout weeks filled** (used) | **15.6%** | **−2.1%** |
| C · true demand (best case, not available in real life) | 15.3% | −2.0% |

## How it works

```
data/ecommerce_demand_weekly.csv
  → fill stockout weeks (average of the last 2 in-stock weeks, history only)
  → features as of each forecast date (recent levels, season, trend, weeks since launch, planned promo)
  → HistGradientBoosting: forecast (Poisson) + p90 (quantile), one pair per horizon
  → rolling backtests: 6 × 4-week folds, 4 × 3-month folds, all covering the Nov peak
  → horizon-total p90 = forecast total × factor from backtest errors (product / category) → data/p90_factors.csv
  → final models forecast every live product from 30 Dec 2024, promo off and on → data/forecasts.csv
  → app.py (promo planner) picks promo-on rows for the PM's promo weeks; revenue net of returns; flags slowing products
```

Promo effects don't carry over between weeks, so precomputing each week with the promo off and on gives exactly the model's answer
without running the model in the browser.

## Limits

- Synthetic data: the method is shown to work; revalidate on real sales.
- Products entering their final decline are over-forecast (+38% at 4 weeks, +73% at 3 months); the planner flags products whose sales are already slowing.
- The 3-month model is weakest in Nov–Dec, the season a Q4 pre-buy is planned for.
- Promo = 25% off only, the one discount depth in the data. Category-wide promos never happened in the history, so that planner result ignores cannibalization (upper bound).
- "Demand to plan for" is a demand figure, not an order quantity: no on-hand stock, lead times or order minimums in the data.
- Snapshot from 30 Dec 2024; production would retrain weekly. Lost sales are treated as lost (no substitution); promos here were random, not chosen.
- No cold-start forecast: no product launched in the 2024 test window.

## Files

| File | What |
|---|---|
| `demand_forecasting.ipynb` | EDA, preprocessing, backtests, final models; writes `data/forecasts.csv` |
| `app.py` | Promo planner (Shiny for Python), reads `data/forecasts.csv` and `data/p90_factors.csv` |
| `data/` | Kaggle CSV, data dictionary, `forecasts.csv`, `p90_factors.csv` |

## Run it

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/jupyter nbconvert --to notebook --execute --inplace demand_forecasting.ipynb   # ~2 min, rewrites data/forecasts.csv
.venv/bin/shiny run app.py
```
