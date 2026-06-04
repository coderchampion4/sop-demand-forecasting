"""
cleaner.py
──────────
Data quality pipeline:
  1. Clamp negative demand to zero
  2. IQR-based outlier capping per SKU (k = OUTLIER_IQR_K)
  3. Inject and repair missing values (simulates real-world gaps)
  4. Export validation report
"""

import numpy as np
import pandas as pd
from config import MISSING_RATE, OUTLIER_IQR_K, RANDOM_SEED, OUTPUT_DIR


def clean_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply full data quality pipeline and write a validation report.

    Parameters
    ----------
    df : pd.DataFrame  Raw demand dataset from data_generator.

    Returns
    -------
    pd.DataFrame  Cleaned, validated dataset.
    """
    np.random.seed(RANDOM_SEED + 1)
    initial_rows = len(df)

    # ── Step 1: Clamp negatives ───────────────────────────────────────────────
    neg_count = (df["demand"] < 0).sum()
    df.loc[df["demand"] < 0, "demand"] = 0

    # ── Step 2: IQR outlier capping per SKU ─────────────────────────────────
    capped_total = 0
    for sku in df["sku_id"].unique():
        mask  = df["sku_id"] == sku
        s     = df.loc[mask, "demand"]
        Q1, Q3 = s.quantile(0.25), s.quantile(0.75)
        upper  = Q3 + OUTLIER_IQR_K * (Q3 - Q1)
        capped = (s > upper).sum()
        capped_total += capped
        df.loc[mask, "demand"] = s.clip(upper=upper)

    # ── Step 3: Inject & repair missing values ────────────────────────────────
    miss_idx    = np.random.choice(df.index, size=int(len(df) * MISSING_RATE), replace=False)
    df.loc[miss_idx, "demand"] = np.nan
    missing_before = int(df["demand"].isna().sum())

    for sku in df["sku_id"].unique():
        mask = df["sku_id"] == sku
        df.loc[mask, "demand"] = df.loc[mask, "demand"].ffill().bfill()
    missing_after = int(df["demand"].isna().sum())

    # ── Step 4: Validation report ────────────────────────────────────────────
    report = {
        "total_records"        : initial_rows,
        "negative_demand_fixed": neg_count,
        "outliers_capped"      : capped_total,
        "missing_injected"     : missing_before,
        "missing_remaining"    : missing_after,
        "discrepancy_rate_pct" : round(missing_after / initial_rows * 100, 4),
    }
    pd.DataFrame([report]).to_csv(f"{OUTPUT_DIR}/validation_report.csv", index=False)

    print(f"[CLEANING]  {initial_rows:,} rows | negatives fixed: {neg_count} "
          f"| outliers capped: {capped_total} | missing: {missing_before} → {missing_after}")
    return df
