# E-commerce Demand Forecasting

Forecast weekly demand per product **4 weeks** and **3 months** ahead, with a **p90** stocking range, and let a PM test a promo
before running it. Two pages on [projects.karthikiyer.info](https://projects.karthikiyer.info/#forecast): the method notebook and
the [promo planner](https://projects.karthikiyer.info/#forecast-app).

**Data:** [E-commerce Demand Forecasting Dataset](https://www.kaggle.com/datasets/sergionefedov/e-commerce-demand-forecasting-dataset)
(Kaggle, CC0), 320 products × 131 weekly rows, Jul 2022 – Dec 2024. **100% synthetic**, which is why it includes the true demand hidden by stockouts.

## Results (rolling backtests, scored against true demand)

| | 4 weeks | 3 months |
|---|---|---|
| Model error (WAPE) | **15.6%** | **19.7%** |
| Best simple rule | 21.6% (last 4 weeks) | 23.8% (level × season) |
| Error cut | −28% | −17% |
| p90 covers actual | 87% of weeks | 88% of weeks |

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
  → final models forecast every live product from 30 Dec 2024, promo off and on → data/forecasts.csv
  → app.py (promo planner) picks promo-on rows for the PM's promo weeks
```

Promo effects don't carry over between weeks, so precomputing each week with the promo off and on gives exactly the model's answer
without running the model in the browser.

## Limits

- Synthetic data: the method is shown to work; revalidate on real sales.
- Products entering their final decline are over-forecast (+39% at 4 weeks, +73% at 3 months); nothing in their history warns of it.
- Promo = 25% off only, the one discount depth in the data.
- p90 covers 87–88%, slightly under its name.
- No cold-start forecast: no product launched in the 2024 test window.

## Files

| File | What |
|---|---|
| `demand_forecasting.ipynb` | EDA, preprocessing, backtests, final models; writes `data/forecasts.csv` |
| `app.py` | Promo planner (Shiny for Python), reads `data/forecasts.csv` |
| `data/` | Kaggle CSV, data dictionary, forecasts |

## Run it

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/jupyter nbconvert --to notebook --execute --inplace demand_forecasting.ipynb   # ~2 min, rewrites data/forecasts.csv
.venv/bin/shiny run app.py
```
