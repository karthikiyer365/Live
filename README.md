# ReLearning — Data Projects

Independent data projects in one repo, each answering a real question with data. Every project is self-contained (own README, data, code).
Live ones are published at **[projects.karthikiyer.info](https://projects.karthikiyer.info)**.

| Project | Status | Type of work | Domain |
|---|---|---|---|
| [E-commerce Sales Dashboard](./ecommerce-sales-dashboard/) | ✅ Live | Dashboarding · Analytics | Commerce · Supply Chain |
| E-commerce Demand Forecasting | ⏳ Next | ML · Time series | Commerce · Supply Chain |
| [Support Ticket Classifier](./topic-classification/) | ✅ Live | ML · NLP | Tech |
| [India EcoPolitical Growth](./indian-ecopolitical-growth/) | ✅ Live | Dashboarding · Data Engineering | Social · Economics |
| [Google Play Store Analysis](./google-playstore-analysis/) | ✅ Complete | Data Science · EDA | Tech |

---

### [E-commerce Sales Dashboard](./ecommerce-sales-dashboard/) · [live](https://projects.karthikiyer.info/#sales)
- **Objective:** Turn 131 weeks of product sales into answers a sales manager can act on Monday.
- **Questions:** Where does revenue come from? When are the peaks? Do promos pay? What do stockouts cost? Which products are dying?
- **Stack:** Kaggle CSV → pandas (`explore.ipynb`) → Shiny for Python + plotly → shinylive (WebAssembly) → GitHub Pages
- **S/T:** Products on sale swung from 4 to 301 a week and moved through launch and decline, so raw totals and growth figures were misleading.
- **A/R:** Compared mature products week for week and promo vs regular weeks of the same product and month. Found promos lose revenue in 6 of 8 categories, stockouts cost $1.71M (3.9%), and a sales-only rule flags dying products ~4 weeks early at 97–98% precision.

### E-commerce Demand Forecasting
- **Objective:** Forecast next month's demand per product and rank stockout exposure.
- **Questions:** What will sell next month? Which products carry the most revenue at risk if they run out?
- **Stack:** Kaggle CSV → pandas → LightGBM + statistical baselines, rolling backtest → notebook rendered to HTML → GitHub Pages
- **S/T (planned):** Observed sales are capped during stockouts, so a model trained on them under-forecasts true demand.
- **A/R (planned):** Forecast `true_demand` with a global model, score against seasonal-naive baselines on a held-out quarter, and report the gain.

### [Support Ticket Classifier](./topic-classification/) · [live](https://projects.karthikiyer.info/#tickets)
- **Objective:** Route a support ticket by type from its text alone.
- **Questions:** Is it an Incident, Request, Problem or Change? When is the model sure enough to route without a person?
- **Stack:** Kaggle CSV → pandas → scikit-learn (TF-IDF + logistic regression) → joblib model + model card → notebook rendered to HTML → GitHub Pages
- **S/T:** The dataset's department labels turned out to be weakly related to the text, and reworded duplicate tickets could leak between train and test.
- **A/R:** Kept each family of reworded tickets on one side of every split and added a confidence gate. 79.9% accuracy on a held-out test; the 46% of tickets above 0.75 confidence auto-route at 96.4%.

### [India EcoPolitical Growth](./indian-ecopolitical-growth/) · [live](https://projects.karthikiyer.info/#india)
- **Objective:** Show what India's growth actually delivered across economy, state, society and politics.
- **Questions:** Did headline GDP reach each person? Did India skip the manufacturing stage? Do prosperity and democracy move together? (14 in total)
- **Stack:** World Bank + IMF + V-Dem → R ETL (config-driven) → parquet → R Shiny + plotly → shinylive (webR) → GitHub Pages
- **S/T:** Most India dashboards stop at GDP; governance data sits in separate sources with different APIs.
- **A/R:** Built one config-driven pipeline over 64 indicators (49 World Bank, 7 IMF, 8 V-Dem) behind 14 questions, published as a serverless browser app that redeploys on every merge.

### [Google Play Store Analysis](./google-playstore-analysis/)
- **Objective:** Find what drives app ratings, installs and survival on the Play Store.
- **Questions:** Which categories dominate? How are ratings and installs distributed? Do privacy policies and developer websites matter?
- **Stack:** Kaggle CSV → pandas + numpy → matplotlib, seaborn, plotly → PDF write-up
- **S/T:** A 2.3M-row raw export with mixed units (M/K/G sizes), duplicate install buckets and missing values.
- **A/R:** Cleaned and unit-normalized the data, engineered app age and trust features, and built 20+ charts. Education is ~20% of all apps, most apps sit at 10–10,000 installs, and a large share has no ratings at all.
