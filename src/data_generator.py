"""
data_generator.py
─────────────────
Generates a synthetic multi-SKU demand dataset with realistic
seasonal patterns, per-SKU trends, and heteroscedastic noise.

Demand model per day:
    demand = base × weekly_factor × annual_factor × trend_factor + N(0, σ)
"""

import numpy as np
import pandas as pd
from config import (
    RANDOM_SEED, START_DATE, END_DATE, N_SKUS, CATEGORIES,
    LEAD_TIMES, UNIT_COSTS, HOLDING_COST_RATE, ORDER_COST_FIXED,
    SEASONAL_MULTIPLIERS, WEEKEND_MULTIPLIER,
)


def generate_demand_dataset() -> pd.DataFrame:
    """
    Generate daily demand records for N_SKUS SKUs across all categories.

    Returns
    -------
    pd.DataFrame
        Columns: date, sku_id, category, demand, lead_time,
                 unit_cost, holding_cost, order_cost
    """
    np.random.seed(RANDOM_SEED)
    date_range = pd.date_range(start=START_DATE, end=END_DATE, freq="D")
    records    = []

    for sku_id in range(1, N_SKUS + 1):
        category     = CATEGORIES[(sku_id - 1) % len(CATEGORIES)]
        base_demand  = np.random.randint(20, 200)
        trend_rate   = np.random.uniform(-0.02, 0.05)
        noise_level  = base_demand * np.random.uniform(0.05, 0.20)

        for i, date in enumerate(date_range):
            weekly_factor  = WEEKEND_MULTIPLIER if date.weekday() >= 5 else 1.0
            annual_factor  = SEASONAL_MULTIPLIERS.get(date.month, SEASONAL_MULTIPLIERS["other"])
            trend_factor   = 1.0 + trend_rate * (i / 365.0)
            noise          = np.random.normal(0, noise_level)

            demand = max(0, round(
                base_demand * weekly_factor * annual_factor * trend_factor + noise
            ))

            records.append({
                "date"        : date,
                "sku_id"      : f"SKU_{sku_id:03d}",
                "category"    : category,
                "demand"      : demand,
                "lead_time"   : LEAD_TIMES[category],
                "unit_cost"   : UNIT_COSTS[category],
                "holding_cost": UNIT_COSTS[category] * HOLDING_COST_RATE,
                "order_cost"  : ORDER_COST_FIXED,
            })

    df = pd.DataFrame(records)
    print(f"[DATA GEN]  {len(df):,} records | {df['sku_id'].nunique()} SKUs "
          f"| {df['category'].nunique()} categories")
    return df
