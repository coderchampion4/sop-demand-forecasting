"""
inventory_optimizer.py
───────────────────────
Calculates optimal inventory parameters per SKU at a 95% service level.

Formulas
--------
  Safety Stock  : SS  = Z × σ_demand × √(lead_time)
  Reorder Point : ROP = avg_daily_demand × lead_time + SS
  EOQ           : EOQ = √(2 × annual_demand × order_cost / holding_cost)

A/B Test
--------
  Policy A (baseline) : ROP = avg_daily × 20  (flat 20-day cover)
  Policy B (optimised): ROP = formula above
  Measure: stockout probability via Normal CDF at each threshold
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
from config import SERVICE_LEVEL_Z, BASELINE_ROP_DAYS


def calculate_inventory_parameters(df: pd.DataFrame, accuracy_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute SS, ROP, EOQ, inventory turnover, and A/B test results per SKU.

    Parameters
    ----------
    df          : Cleaned demand DataFrame
    accuracy_df : Forecast accuracy summary (for joining category metadata)

    Returns
    -------
    pd.DataFrame  Inventory parameter table — one row per SKU
    """
    records = []

    for sku, grp in df.groupby("sku_id"):
        daily        = grp.set_index("date")["demand"].resample("D").sum()
        lead_time    = int(grp["lead_time"].iloc[0])
        unit_cost    = float(grp["unit_cost"].iloc[0])
        holding_cost = float(grp["holding_cost"].iloc[0])
        order_cost   = float(grp["order_cost"].iloc[0])
        annual_demand= daily.mean() * 365

        avg_daily    = daily.mean()
        std_daily    = daily.std()

        # ── Core inventory metrics ────────────────────────────────────────────
        safety_stock  = SERVICE_LEVEL_Z * std_daily * np.sqrt(lead_time)
        rop_optimised = avg_daily * lead_time + safety_stock
        rop_baseline  = avg_daily * BASELINE_ROP_DAYS
        eoq           = np.sqrt(max(0, 2 * annual_demand * order_cost / holding_cost))
        inv_turnover  = annual_demand / max(eoq / 2 + safety_stock, 1)

        # ── A/B stockout probability via Normal CDF ────────────────────────
        demand_during_lt_mean = avg_daily * lead_time
        demand_during_lt_std  = std_daily * np.sqrt(lead_time)

        p_stockout_baseline  = 1.0 - norm.cdf(rop_baseline,  demand_during_lt_mean, max(demand_during_lt_std, 1e-6))
        p_stockout_optimised = 1.0 - norm.cdf(rop_optimised, demand_during_lt_mean, max(demand_during_lt_std, 1e-6))
        stockout_reduction   = (
            (p_stockout_baseline - p_stockout_optimised) / max(p_stockout_baseline, 1e-9) * 100
        )

        records.append({
            "sku_id"                     : sku,
            "category"                   : grp["category"].iloc[0],
            "avg_daily_demand"           : round(avg_daily, 2),
            "demand_std_dev"             : round(std_daily, 2),
            "lead_time_days"             : lead_time,
            "safety_stock_units"         : int(round(safety_stock)),
            "reorder_point_optimised"    : int(round(rop_optimised)),
            "reorder_point_baseline"     : int(round(rop_baseline)),
            "eoq_units"                  : int(round(eoq)),
            "inventory_turnover"         : round(inv_turnover, 2),
            "stockout_prob_baseline_pct" : round(p_stockout_baseline  * 100, 2),
            "stockout_prob_optimised_pct": round(p_stockout_optimised * 100, 2),
            "stockout_reduction_pct"     : round(stockout_reduction, 2),
        })

    inv_df = pd.DataFrame(records)
    print(f"[INVENTORY] {len(inv_df)} SKUs | Avg stockout risk (optimised): "
          f"{inv_df['stockout_prob_optimised_pct'].mean():.2f}%")
    return inv_df
