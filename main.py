"""
main.py — S&OP Demand Forecasting & Inventory Optimisation Engine
─────────────────────────────────────────────────────────────────
Entry point. Runs the full pipeline end-to-end.

Usage
─────
    python main.py

Outputs → outputs/
"""

import time
from src import (
    generate_demand_dataset,
    clean_and_validate,
    forecast_all_skus,
    calculate_inventory_parameters,
    generate_sop_kpi_export,
)

BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║   S&OP DEMAND FORECASTING & INVENTORY OPTIMISATION ENGINE        ║
║   Author : Ashmit Goel                                           ║
║   Tools  : Python | SQL | Power BI                               ║
╚══════════════════════════════════════════════════════════════════╝
"""

def main():
    print(BANNER)
    t0 = time.time()

    # ── Stage 1: Generate data ────────────────────────────────────────────────
    print("▶  Stage 1/5 — Data Generation")
    df = generate_demand_dataset()

    # ── Stage 2: Clean & validate ─────────────────────────────────────────────
    print("\n▶  Stage 2/5 — Data Cleaning & Validation")
    df = clean_and_validate(df)

    # ── Stage 3: Demand forecasting ───────────────────────────────────────────
    print("\n▶  Stage 3/5 — Demand Forecasting (3-model horse race)")
    forecast_df, accuracy_df = forecast_all_skus(df)

    # ── Stage 4: Inventory optimisation ──────────────────────────────────────
    print("\n▶  Stage 4/5 — Inventory Parameter Optimisation")
    inv_df = calculate_inventory_parameters(df, accuracy_df)

    # ── Stage 5: Export ───────────────────────────────────────────────────────
    print("\n▶  Stage 5/5 — Exporting Power BI-Ready Outputs")
    kpi_df = generate_sop_kpi_export(df, forecast_df, inv_df, accuracy_df)

    # ── Summary ───────────────────────────────────────────────────────────────
    elapsed = time.time() - t0
    print(f"\n{'─'*65}")
    print("  S&OP KPI SUMMARY BY CATEGORY")
    print(f"{'─'*65}")
    print(kpi_df[["category","avg_inv_turnover","avg_stockout_opt","avg_mape"]].to_string(index=False))
    print(f"\n  Pipeline completed in {elapsed:.1f}s")
    print(f"{'─'*65}")


if __name__ == "__main__":
    main()
