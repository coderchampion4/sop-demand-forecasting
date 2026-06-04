"""
exporter.py
───────────
Generates all Power BI-ready CSV exports and the S&OP KPI summary.

Output files
------------
  weekly_demand_actuals.csv  — aggregated weekly demand by category
  30day_demand_forecast.csv  — daily forward forecasts per SKU
  inventory_parameters.csv   — SS, ROP, EOQ, turnover per SKU
  forecast_accuracy.csv      — model selection & accuracy per SKU
  sop_kpi_summary.csv        — category-level KPI scorecard
"""

import os
import pandas as pd
from config import OUTPUT_DIR


def generate_sop_kpi_export(
    df          : pd.DataFrame,
    forecast_df : pd.DataFrame,
    inv_df      : pd.DataFrame,
    accuracy_df : pd.DataFrame,
) -> pd.DataFrame:
    """
    Aggregate all pipeline outputs into Power BI-ready CSVs.

    Returns
    -------
    pd.DataFrame  Category-level S&OP KPI summary
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── Weekly demand actuals ─────────────────────────────────────────────────
    weekly = df.copy()
    weekly["week"] = weekly["date"].dt.to_period("W").apply(lambda x: x.start_time)
    weekly_agg = (
        weekly.groupby(["week", "category"])
        .agg(total_demand=("demand","sum"), avg_daily_demand=("demand","mean"))
        .reset_index()
    )

    # ── Category-level KPI summary ────────────────────────────────────────────
    inv_cat = (
        inv_df.groupby("category")
        .agg(
            avg_safety_stock     =("safety_stock_units",          "mean"),
            avg_inv_turnover     =("inventory_turnover",           "mean"),
            avg_stockout_baseline=("stockout_prob_baseline_pct",   "mean"),
            avg_stockout_opt     =("stockout_prob_optimised_pct",  "mean"),
        )
        .reset_index()
    )
    acc_cat = (
        accuracy_df.merge(inv_df[["sku_id","category"]], on="sku_id")
        .groupby("category")
        .agg(avg_mape=("mape_best_pct","mean"), avg_mae=("mae","mean"))
        .reset_index()
    )
    kpi_df = inv_cat.merge(acc_cat, on="category").round(2)

    # ── Write outputs ─────────────────────────────────────────────────────────
    files = {
        "weekly_demand_actuals.csv" : weekly_agg,
        "30day_demand_forecast.csv" : forecast_df,
        "inventory_parameters.csv"  : inv_df,
        "forecast_accuracy.csv"     : accuracy_df,
        "sop_kpi_summary.csv"       : kpi_df,
    }
    for fname, frame in files.items():
        path = os.path.join(OUTPUT_DIR, fname)
        frame.to_csv(path, index=False)
        print(f"[EXPORT]    {fname:40s} ({len(frame):,} rows)")

    return kpi_df
