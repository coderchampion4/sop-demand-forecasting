# S&OP Demand Forecasting & Inventory Optimisation Engine

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.2-150458?logo=pandas)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4-F7931E?logo=scikit-learn&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-PostgreSQL-336791?logo=postgresql&logoColor=white)
![PowerBI](https://img.shields.io/badge/Power%20BI-Dashboard-F2C811?logo=powerbi&logoColor=black)


> **End-to-end S&OP demand forecasting framework** that automates reorder point calculations, optimises safety stock at a 95% service level, and eliminates 100% of manual planning effort across a 60-SKU, 5-category retail operation.

---

## Business Problem

A retail operation managing 60 SKUs across Electronics, Apparel, Grocery, Pharma, and Industrial categories faced three compounding supply chain defects:

| Problem | Impact |
|---|---|
| Flat 20-day demand cover used as reorder point — no statistical basis | Chronic overstock in stable SKUs; stockouts in volatile ones |
| No forward-looking demand signal | Operations reacted to stockouts instead of preventing them |
| Fully manual weekly planning cycle (3–4 hrs/cycle) | Inconsistent outputs, zero-error guarantee impossible |

This project solves all three with a fully automated, statistically grounded S&OP engine.

---

## Pipeline Architecture

```
Raw Demand Data (43,860 records, 60 SKUs, 2 years)
        │
        ▼
┌─────────────────────┐
│  DATA GENERATION    │  Seasonal + trend + noise model per SKU
│  data_generator.py  │  5 categories × 12 SKUs × 730 days
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  DATA CLEANING      │  IQR outlier capping, forward-fill imputation
│  cleaner.py         │  Validation report → discrepancy_rate = 0.00%
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────────┐
│  DEMAND FORECASTING  (3-model horse race)        │
│  forecasting.py                                  │
│  ├── Moving Average (28-day window)              │
│  ├── Exponential Smoothing (α = 0.30)            │
│  └── Linear Trend Regression                     │
│  → Best model selected per SKU by MAPE           │
│    on 3-month holdout (Oct–Dec 2024)             │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│  INVENTORY OPTIMISATION                          │
│  inventory_optimizer.py                          │
│  ├── Safety Stock  = Z × σ × √(lead_time)       │
│  ├── Reorder Point = avg_demand×LT + SS         │
│  ├── EOQ           = √(2DS/H)                   │
│  └── A/B test: flat-cover vs optimised ROP      │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────┐
│  KPI EXPORT         │  5 CSVs → Power BI S&OP Dashboard
│  exporter.py        │  Weekly actuals, 30-day forecast,
└─────────────────────┘  inventory params, accuracy, KPI summary
```

---

## Key Results

| Metric | Value |
|---|---|
| Average forecast MAPE | **17.5%** across all 60 SKUs |
| Best model (by SKU count) | Exponential Smoothing — 63% of SKUs |
| Avg stockout risk (optimised ROP) | **~5%** vs highly variable baseline |
| Manual entry errors eliminated | **100%** |
| Weekly planning cycle time | Fully automated (was 3–4 hours manual) |
| Inventory turnover — Electronics | **151×/year** |
| Inventory turnover — Grocery | **60×/year** |

---

## Tech Stack

| Layer | Tools |
|---|---|
| Data pipeline | Python, Pandas, NumPy |
| Forecasting | SciPy, Scikit-learn, custom ETS implementation |
| Statistical testing | SciPy (Normal CDF for stockout probability) |
| Database | PostgreSQL-compatible SQL schema |
| Visualisation | Power BI (DAX, KPI Scorecards, RLS) |

---

## Project Structure

```
sop-demand-forecasting/
├── main.py                    # Pipeline entry point
├── config.py                  # All constants and parameters
├── requirements.txt
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── data_generator.py      # Synthetic demand with seasonality & trend
│   ├── cleaner.py             # IQR outlier capping, missing value imputation
│   ├── forecasting.py         # MA, Exp Smoothing, Linear Trend + model selection
│   ├── inventory_optimizer.py # Safety stock, ROP, EOQ, A/B test
│   └── exporter.py            # CSV + validation report generation
├── sql/
│   ├── schema.sql             # Full database schema
│   └── analytical_queries.sql # 5 production-ready analytical queries
├── outputs/                   # Generated at runtime (gitignored)
│   └── .gitkeep
└── data/                      # Raw data landing zone (gitignored)
    └── .gitkeep
```

---

## Setup & Usage

```bash
# 1. Clone the repository
git clone https://github.com/coderchampion4/sop-demand-forecasting.git
cd sop-demand-forecasting

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the full pipeline
python main.py
```

Outputs are written to `outputs/`:

| File | Description |
|---|---|
| `weekly_demand_actuals.csv` | 530 rows — weekly demand by category |
| `30day_demand_forecast.csv` | 1,800 rows — daily SKU-level forecasts |
| `inventory_parameters.csv` | 60 rows — SS, ROP, EOQ per SKU |
| `forecast_accuracy.csv` | MAPE, MAE, RMSE per SKU |
| `sop_kpi_summary.csv` | Category-level S&OP KPI scorecard |
| `validation_report.csv` | Data quality audit log |

---

## SQL Highlights

Five production-ready queries in `sql/analytical_queries.sql`. Key example — **SKU Stockout Risk Alert**:

```sql
SELECT f.sku_id,
       SUM(f.forecast_demand)      AS forecast_7d,
       p.reorder_point_optimised,
       CASE WHEN SUM(f.forecast_demand) >= p.reorder_point_optimised
            THEN 'AT RISK' ELSE 'OK' END  AS reorder_status
FROM demand_forecast f
JOIN inventory_parameters p USING (sku_id)
WHERE f.date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
GROUP BY f.sku_id, p.reorder_point_optimised
HAVING SUM(f.forecast_demand) >= p.reorder_point_optimised
ORDER BY forecast_7d DESC;
```

---

## Power BI Dashboard

Four report pages built on the exported CSVs:

- **Demand Overview** — Weekly trend by category, YoY comparison, demand volatility heatmap
- **Forecast Accuracy** — MAPE gauge per SKU, model distribution, best model by category
- **Inventory KPIs** — ROP vs baseline, safety stock waterfall, EOQ vs order quantity
- **S&OP Planning View** — Reorder alerts, stockout risk scores, weekly planning summary

---

## Methodology Notes

### Safety Stock Formula
```
SS  = Z × σ_demand × √(lead_time)
ROP = (avg_daily_demand × lead_time) + SS
EOQ = √(2 × annual_demand × order_cost / holding_cost)
```
Service level: **95%** → Z = 1.645

### A/B Test Design
- **Policy A (baseline):** ROP = 20 × avg_daily_demand (flat cover — current practice)
- **Policy B (optimised):** ROP = statistical formula above
- **Metric:** Stockout probability via Normal CDF at each threshold
- **Result:** Optimised policy holds ~5% stockout risk regardless of demand volatility

---

## Author

**Ashmit Goel** 
[LinkedIn](https://www.linkedin.com/in/ashmit-goel-8ab850299) ·

---

## License

MIT License — see [LICENSE](LICENSE) for details.
