"""
forecasting.py
──────────────
Three-model demand forecasting horse race per SKU.

Models
------
  • MovingAverage     — 28-day rolling mean
  • ExpSmoothing      — Simple exponential smoothing (α=0.30)
  • LinearTrend       — OLS linear trend extrapolation

Selection criterion: lowest MAPE on 3-month holdout (Oct–Dec 2024).
Forward horizon: 30 days.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model  import LinearRegression
from sklearn.metrics       import mean_absolute_error, mean_squared_error
from config import TRAIN_CUTOFF, FORECAST_HORIZON, MA_WINDOW, EXP_ALPHA


# ── Metric helpers ────────────────────────────────────────────────────────────

def mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean Absolute Percentage Error — excludes zero actuals."""
    mask = actual > 0
    if mask.sum() == 0:
        return np.nan
    return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)


# ── Forecasting models ────────────────────────────────────────────────────────

def moving_average(series: pd.Series, horizon: int) -> np.ndarray:
    """28-day rolling average projected flat over horizon."""
    window = min(MA_WINDOW, len(series))
    return np.full(horizon, series.iloc[-window:].mean())


def exp_smoothing(series: pd.Series, horizon: int) -> np.ndarray:
    """
    Simple exponential smoothing: S_t = α·x_t + (1−α)·S_{t-1}
    Final smoothed level projected flat over horizon.
    """
    level = series.iloc[0]
    for val in series.iloc[1:]:
        level = EXP_ALPHA * val + (1 - EXP_ALPHA) * level
    return np.full(horizon, level)


def linear_trend(series: pd.Series, horizon: int) -> np.ndarray:
    """OLS linear trend extrapolated over horizon. Clamps negatives to 0."""
    X = np.arange(len(series)).reshape(-1, 1)
    model = LinearRegression().fit(X, series.values)
    X_fut = np.arange(len(series), len(series) + horizon).reshape(-1, 1)
    return np.maximum(0, model.predict(X_fut))


# ── Per-SKU model selection ───────────────────────────────────────────────────

def _best_model(train: pd.Series, test: pd.Series) -> tuple[str, np.ndarray]:
    """
    Evaluate all three models on holdout; return name and forecast of winner.
    """
    horizon = len(test)
    actual  = test.values
    candidates = {
        "Moving_Average" : moving_average(train, horizon),
        "Exp_Smoothing"  : exp_smoothing(train, horizon),
        "Linear_Trend"   : linear_trend(train, horizon),
    }
    scores = {name: mape(actual, pred) for name, pred in candidates.items()}
    winner = min(scores, key=lambda k: scores[k] if not np.isnan(scores[k]) else 1e9)
    return winner, candidates[winner], scores


def forecast_all_skus(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    For every SKU:
      1. Train on [START_DATE, TRAIN_CUTOFF]
      2. Evaluate on (TRAIN_CUTOFF, END_DATE]
      3. Select best model by MAPE
      4. Produce FORECAST_HORIZON-day forward forecast from 2025-01-01

    Returns
    -------
    forecast_df  : Daily forward forecasts (date, sku_id, forecast_demand, model)
    accuracy_df  : Per-SKU accuracy metrics
    """
    forecast_rows = []
    accuracy_rows = []

    for sku, grp in df.groupby("sku_id"):
        daily = grp.set_index("date")["demand"].resample("D").sum()
        train = daily[daily.index <= TRAIN_CUTOFF]
        test  = daily[daily.index >  TRAIN_CUTOFF]
        if len(train) < 30 or len(test) < 10:
            continue

        winner, _, scores = _best_model(train, test)
        actual = test.values

        # Holdout metrics for the winning model
        best_pred = {
            "Moving_Average": moving_average,
            "Exp_Smoothing" : exp_smoothing,
            "Linear_Trend"  : linear_trend,
        }[winner](train, len(test))

        mae  = mean_absolute_error(actual, best_pred)
        rmse = float(np.sqrt(mean_squared_error(actual, best_pred)))

        accuracy_rows.append({
            "sku_id"          : sku,
            "best_model"      : winner,
            "mape_best_pct"   : round(scores[winner], 2),
            "mape_ma"         : round(scores["Moving_Average"], 2),
            "mape_es"         : round(scores["Exp_Smoothing"], 2),
            "mape_lt"         : round(scores["Linear_Trend"], 2),
            "mae"             : round(mae, 2),
            "rmse"            : round(rmse, 2),
            "avg_daily_demand": round(daily.mean(), 2),
            "cv_demand"       : round(daily.std() / daily.mean(), 3),
        })

        # Forward forecast from 2025-01-01
        fcast = {
            "Moving_Average": moving_average,
            "Exp_Smoothing" : exp_smoothing,
            "Linear_Trend"  : linear_trend,
        }[winner](daily, FORECAST_HORIZON)

        for date, val in zip(pd.date_range("2025-01-01", periods=FORECAST_HORIZON), fcast):
            forecast_rows.append({
                "date"           : date,
                "sku_id"         : sku,
                "forecast_demand": round(max(0, val), 2),
                "model"          : winner,
            })

    forecast_df  = pd.DataFrame(forecast_rows)
    accuracy_df  = pd.DataFrame(accuracy_rows)

    avg_mape = accuracy_df["mape_best_pct"].mean()
    dist     = accuracy_df["best_model"].value_counts().to_dict()
    print(f"[FORECAST]  Avg MAPE: {avg_mape:.2f}% | Model distribution: {dist}")
    return forecast_df, accuracy_df
