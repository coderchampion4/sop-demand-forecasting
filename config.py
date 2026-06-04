# =============================================================================
# config.py — Centralised configuration for the S&OP forecasting pipeline
# =============================================================================

import os

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
DATA_DIR   = os.path.join(BASE_DIR, "data")

# ── Dataset parameters ────────────────────────────────────────────────────────
RANDOM_SEED    = 42
START_DATE     = "2023-01-01"
END_DATE       = "2024-12-31"
N_SKUS         = 60
CATEGORIES     = ["Electronics", "Apparel", "Grocery", "Pharma", "Industrial"]

LEAD_TIMES = {
    "Electronics": 7,
    "Apparel"    : 14,
    "Grocery"    : 3,
    "Pharma"     : 5,
    "Industrial" : 10,
}

UNIT_COSTS = {
    "Electronics": 120,
    "Apparel"    : 45,
    "Grocery"    : 8,
    "Pharma"     : 25,
    "Industrial" : 60,
}

HOLDING_COST_RATE = 0.25   # 25% of unit cost per year
ORDER_COST_FIXED  = 50     # USD per order

# ── Data quality ──────────────────────────────────────────────────────────────
MISSING_RATE  = 0.005      # 0.5% of records will have injected nulls
OUTLIER_IQR_K = 3.0        # Cap outliers beyond Q3 + k*IQR

# ── Seasonal multipliers ─────────────────────────────────────────────────────
SEASONAL_MULTIPLIERS = {
    12      : 1.40,
    11      : 1.15,
    1       : 1.15,
    6       : 0.85,
    7       : 0.85,
    "other" : 1.00,
}
WEEKEND_MULTIPLIER = 1.20

# ── Forecasting ───────────────────────────────────────────────────────────────
TRAIN_CUTOFF      = "2024-09-30"   # 21-month train, 3-month holdout
FORECAST_HORIZON  = 30             # days forward
MA_WINDOW         = 28             # Moving average window
EXP_ALPHA         = 0.30           # Exponential smoothing alpha

# ── Inventory optimisation ────────────────────────────────────────────────────
SERVICE_LEVEL_Z   = 1.645          # 95% service level
BASELINE_ROP_DAYS = 20             # Current flat-cover policy (days of avg demand)
