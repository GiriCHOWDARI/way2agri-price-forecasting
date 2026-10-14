from __future__ import annotations
from pathlib import Path
import json
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import Holt, ExponentialSmoothing

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "price_data.csv"
MODEL_PATH = Path(__file__).resolve().parents[1] / "data" / "active_model.json"
REQUIRED_COLUMNS = {"date", "avg_monthly_price"}

class DataValidationError(ValueError):
    pass

def load_monthly_series(path: Path = DATA_PATH) -> pd.Series:
    if not path.exists():
        raise DataValidationError(f"Dataset not found: {path}")
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise DataValidationError("Could not read the CSV file.") from exc
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise DataValidationError(f"Missing required CSV columns: {sorted(missing)}")
    df = df[["date", "avg_monthly_price"]].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["avg_monthly_price"] = pd.to_numeric(df["avg_monthly_price"], errors="coerce")
    if df[["date", "avg_monthly_price"]].isna().any().any():
        raise DataValidationError("Date and price columns must contain valid, non-empty values.")
    if df.empty:
        raise DataValidationError("No valid observations found in the CSV.")
    if not np.isfinite(df["avg_monthly_price"].to_numpy(dtype=float)).all():
        raise DataValidationError("Prices must be finite numeric values.")
    if (df["avg_monthly_price"] <= 0).any():
        raise DataValidationError("Prices must be positive.")
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()
    if df["date"].duplicated().any():
        raise DataValidationError("Multiple rows exist for a month. Filter by commodity/market or aggregate explicitly.")
    df = df.sort_values("date").set_index("date")
    full_index = pd.date_range(df.index.min(), df.index.max(), freq="MS")
    df = df.reindex(full_index)
    df.index.name = "date"
    if df["avg_monthly_price"].isna().any():
        missing_months = df.index[df["avg_monthly_price"].isna()].strftime("%Y-%m").tolist()
        raise DataValidationError(f"Missing monthly observations: {missing_months[:12]}")
    if len(df) < 24:
        raise DataValidationError("At least 24 monthly observations are required.")
    return df["avg_monthly_price"].astype(float)

def _forecast_candidate(series: pd.Series, horizon: int, model_name: str) -> np.ndarray:
    values = np.asarray(series, dtype=float)
    if model_name == "Naive baseline":
        return np.repeat(values[-1], horizon)
    if model_name == "Drift":
        drift = (values[-1] - values[0]) / max(len(values) - 1, 1)
        return values[-1] + drift * np.arange(1, horizon + 1)
    if model_name == "Holt damped trend":
        fitted = Holt(series, damped_trend=True, initialization_method="estimated").fit(optimized=True)
        return np.asarray(fitted.forecast(horizon), dtype=float)
    if model_name == "Holt-Winters additive":
        fitted = ExponentialSmoothing(series, trend="add", seasonal="add", seasonal_periods=12,
                                      initialization_method="estimated").fit(optimized=True)
        return np.asarray(fitted.forecast(horizon), dtype=float)
    raise ValueError(f"Unknown forecasting model: {model_name}")

def _active_model() -> str:
    if MODEL_PATH.exists():
        try:
            name = json.loads(MODEL_PATH.read_text(encoding="utf-8")).get("selected_model")
            if name in {"Naive baseline", "Drift", "Holt damped trend", "Holt-Winters additive"}:
                return name
        except (OSError, json.JSONDecodeError):
            pass
    return "Naive baseline"

def build_forecast(series: pd.Series, horizon: int = 12) -> dict:
    if not 1 <= horizon <= 36:
        raise ValueError("horizon must be between 1 and 36 months.")
    model_name = _active_model()
    try:
        predictions = _forecast_candidate(series, horizon, model_name)
    except Exception:
        # Fail safely to a transparent baseline if a fitted model cannot be produced.
        model_name = "Naive baseline (safe fallback)"
        predictions = np.repeat(float(series.iloc[-1]), horizon)
    last_date = pd.Timestamp(series.index.max())
    last_value = float(series.iloc[-1])
    dates = pd.date_range(last_date + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    age_days = (pd.Timestamp.now(tz=None).normalize() - last_date.normalize()).days
    return {
        "model": model_name,
        "horizon_months": horizon,
        "last_observation_date": last_date.strftime("%Y-%m-%d"),
        "last_observed_price": round(last_value, 2),
        "data_age_days": max(0, int(age_days)),
        "is_stale": age_days > 62,
        "forecast": [{"date": d.strftime("%Y-%m-%d"), "predicted_price": round(float(max(0, p)), 2)} for d, p in zip(dates, predictions)],
        "limitations": [
            "Model selection uses historical rolling-origin validation; recent structural changes can invalidate it.",
            "Forecast uncertainty intervals and commodity/market metadata are not yet implemented.",
            "Forecasts are decision support only; do not automate purchasing from this output.",
        ],
    }

# Backwards-compatible function name used by existing code/tests.
def build_naive_forecast(series: pd.Series, horizon: int = 12) -> dict:
    return build_forecast(series, horizon)

def evaluate_and_select_model(series: pd.Series, windows: int = 4, horizon: int = 12) -> dict:
    """Chronological expanding-window validation. Selection prioritizes mean MAE."""
    candidates = ["Naive baseline", "Drift", "Holt damped trend", "Holt-Winters additive"]
    if len(series) < horizon * 2 + 12:
        raise ValueError(f"At least {horizon * 2 + 12} observations are needed for this validation setup.")
    max_windows = min(windows, (len(series) - 24) // horizon)
    if max_windows < 1:
        raise ValueError("Not enough history for rolling-origin validation.")
    rows = []
    for model_name in candidates:
        maes, rmses, mapes = [], [], []
        successful = True
        for window in range(max_windows, 0, -1):
            test_end = len(series) - (window - 1) * horizon
            test_start = test_end - horizon
            train = series.iloc[:test_start]
            actual = np.asarray(series.iloc[test_start:test_end], dtype=float)
            try:
                pred = _forecast_candidate(train, len(actual), model_name)
                errors = actual - pred
                maes.append(float(np.mean(np.abs(errors))))
                rmses.append(float(np.sqrt(np.mean(errors ** 2))))
                mapes.append(float(np.mean(np.abs(errors / actual)) * 100))
            except Exception:
                successful = False
                break
        if successful and maes:
            rows.append({"model": model_name, "windows_evaluated": len(maes),
                         "mean_mae": round(float(np.mean(maes)), 2),
                         "mean_rmse": round(float(np.mean(rmses)), 2),
                         "mean_mape_percent": round(float(np.mean(mapes)), 2)})
    if not rows:
        raise ValueError("All candidate models failed validation.")
    rows.sort(key=lambda row: (row["mean_mae"], row["mean_mape_percent"]))
    selected = rows[0]["model"]
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(json.dumps({"selected_model": selected, "selection_metric": "mean_mae",
        "validation_horizon_months": horizon, "windows_evaluated": max_windows,
        "observation_count": int(len(series)), "last_observation_date": series.index.max().strftime("%Y-%m-%d"),
        "results": rows}, indent=2), encoding="utf-8")
    return {"selected_model": selected, "selection_metric": "mean_mae", "validation_horizon_months": horizon,
            "windows_evaluated": max_windows, "observation_count": int(len(series)),
            "last_observation_date": series.index.max().strftime("%Y-%m-%d"), "results": rows,
            "warning": "Historical validation does not guarantee future performance. Review metrics and business thresholds before operational use."}
