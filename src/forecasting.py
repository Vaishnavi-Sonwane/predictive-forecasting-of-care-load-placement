"""Weekly forecasting utilities for the UAC public reporting series."""
from __future__ import annotations

from dataclasses import dataclass
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor

DATE = "Date"
CARE = "Children in HHS Care"
DISCHARGES = "Children discharged from HHS Care"
TRANSFERS = "Children transferred out of CBP custody"
INTAKE = "Children apprehended and placed in CBP custody*"
CBP_STOCK = "Children in CBP custody"
NUMERIC = [INTAKE, CBP_STOCK, TRANSFERS, CARE, DISCHARGES]
MODEL_NAMES = ["Persistence", "4-week average", "Exponential smoothing", "Random forest", "Gradient boosting"]


@dataclass
class PreparedData:
    weekly: pd.DataFrame
    quality: dict
    source: pd.DataFrame


def load_data(path: str) -> PreparedData:
    raw = pd.read_csv(path, thousands=",")
    original_rows = len(raw)
    raw = raw.dropna(how="all").copy()
    raw[DATE] = pd.to_datetime(raw[DATE], errors="coerce")
    bad_dates = int(raw[DATE].isna().sum())
    raw = raw.dropna(subset=[DATE]).copy()
    for col in NUMERIC:
        raw[col] = pd.to_numeric(raw[col], errors="coerce")
    raw = raw.dropna(subset=[CARE, DISCHARGES]).sort_values(DATE)
    duplicates = int(raw.duplicated(DATE, keep="last").sum())
    raw = raw.drop_duplicates(DATE, keep="last").set_index(DATE)
    if raw.empty:
        raise ValueError("No valid dated observations were found in the input file.")

    # Stock is a point-in-time snapshot; flow fields remain observed values.
    weekly = pd.DataFrame(index=raw[CARE].resample("W-SUN").last().index)
    weekly[CARE] = raw[CARE].resample("W-SUN").last()
    weekly["reported_days"] = raw[CARE].resample("W-SUN").count()
    weekly[DISCHARGES] = raw[DISCHARGES].resample("W-SUN").mean() * 7
    weekly[TRANSFERS] = raw[TRANSFERS].resample("W-SUN").mean() * 7
    weekly[INTAKE] = raw[INTAKE].resample("W-SUN").mean() * 7
    weekly[CBP_STOCK] = raw[CBP_STOCK].resample("W-SUN").last()
    weekly["net_pressure"] = weekly[TRANSFERS] - weekly[DISCHARGES]
    # Only bridge a single missing weekly snapshot; longer gaps stay missing.
    weekly[CARE] = weekly[CARE].interpolate(limit=1, limit_area="inside")
    weekly["care_interpolated"] = weekly[CARE].notna() & weekly["reported_days"].eq(0)
    usable = weekly.dropna(subset=[CARE, DISCHARGES]).copy()
    quality = {
        "source_rows": original_rows,
        "blank_rows_removed": original_rows - len(raw) - bad_dates - duplicates,
        "invalid_date_rows": bad_dates,
        "duplicate_dates": duplicates,
        "observations": len(raw),
        "start": raw.index.min(),
        "end": raw.index.max(),
        "calendar_days": (raw.index.max() - raw.index.min()).days + 1,
        "reporting_coverage_pct": 100 * len(raw) / ((raw.index.max() - raw.index.min()).days + 1),
        "weekly_points": len(usable),
        "weeks_interpolated": int(weekly["care_interpolated"].sum()),
        "median_gap_days": float(raw.index.to_series().diff().dt.days.median()),
        "max_gap_days": int(raw.index.to_series().diff().dt.days.max()),
    }
    return PreparedData(usable, quality, raw.reset_index())


def _features(y: pd.Series, index: int) -> list[float]:
    vals = y.iloc[:index]
    def lag(k: int) -> float:
        return float(vals.iloc[-k]) if len(vals) >= k else float(vals.iloc[-1])
    return [lag(1), lag(2), lag(4), lag(8), lag(13), float(vals.tail(4).mean()),
            float(vals.tail(8).mean()), float(vals.tail(4).std(ddof=0) if len(vals.tail(4)) > 1 else 0),
            float(index % 52), float(np.sin(2 * np.pi * (index % 52) / 52)),
            float(np.cos(2 * np.pi * (index % 52) / 52))]


def _recursive_model(y: pd.Series, horizon: int, estimator) -> np.ndarray:
    values = list(map(float, y))
    training = pd.Series(values)
    x = np.asarray([_features(training, i) for i in range(8, len(training))])
    target = np.asarray(values[8:])
    fitted = len(target) >= 10
    if fitted:
        estimator.fit(x, target)
    out = []
    for step in range(horizon):
        if not fitted:
            pred = values[-1]
        else:
            pred = float(estimator.predict(np.asarray([_features(pd.Series(values), len(values))]))[0])
        values.append(max(0.0, pred))
        out.append(values[-1])
    return np.asarray(out)


def forecast_one(y: pd.Series, horizon: int, model: str) -> np.ndarray:
    y = y.dropna().astype(float)
    if len(y) < 10:
        raise ValueError("At least 10 weekly observations are required to forecast.")
    if model == "Persistence":
        return np.repeat(y.iloc[-1], horizon)
    if model == "4-week average":
        return np.repeat(y.tail(4).mean(), horizon)
    if model == "Exponential smoothing":
        # Damped level/trend smoother fit using a small grid; avoids external state-space dependencies.
        best = (float("inf"), float(y.iloc[-1]), 0.0)
        arr = y.to_numpy()
        for alpha in (0.15, 0.3, 0.5, 0.7):
            for beta in (0.0, 0.1, 0.25):
                level, trend = arr[0], arr[1] - arr[0]
                err = []
                for actual in arr[1:]:
                    pred = level + 0.8 * trend
                    err.append((actual - pred) ** 2)
                    prev = level
                    level = alpha * actual + (1 - alpha) * pred
                    trend = beta * (level - prev) + (1 - beta) * 0.8 * trend
                score = float(np.mean(err[-min(26, len(err)):]))
                if score < best[0]: best = (score, level, trend)
        _, level, trend = best
        return np.maximum(0, np.asarray([level + sum((0.8 ** j) * trend for j in range(1, k + 1)) for k in range(1, horizon + 1)]))
    if model == "Random forest":
        return _recursive_model(y, horizon, RandomForestRegressor(n_estimators=250, min_samples_leaf=3, max_features=0.8, random_state=42, n_jobs=-1))
    if model == "Gradient boosting":
        return _recursive_model(y, horizon, GradientBoostingRegressor(n_estimators=120, max_depth=2, learning_rate=0.035, loss="huber", random_state=42))
    raise ValueError(f"Unknown model: {model}")


def walk_forward(y: pd.Series, max_horizon: int = 4, folds: int = 20) -> pd.DataFrame:
    y = y.dropna().astype(float)
    starts = list(range(max(20, len(y) - max_horizon - folds + 1), len(y) - max_horizon + 1))
    rows = []
    for origin in starts:
        train = y.iloc[:origin]
        for model in MODEL_NAMES:
            try:
                predictions = forecast_one(train, max_horizon, model)
            except Exception as exc:
                warnings.warn(f"Skipping {model} at origin {origin}: {exc}")
                continue
            for h, prediction in enumerate(predictions, start=1):
                actual = float(y.iloc[origin + h - 1])
                rows.append({"horizon_weeks": h, "model": model, "actual": actual, "prediction": float(prediction),
                             "origin": y.index[origin - 1], "target_date": y.index[origin + h - 1]})
    return pd.DataFrame(rows)


def score_forecasts(backtest: pd.DataFrame) -> pd.DataFrame:
    if backtest.empty:
        return pd.DataFrame(columns=["horizon_weeks", "model", "MAE", "RMSE", "MAPE_pct", "n"])
    b = backtest.copy()
    b["abs_error"] = (b.actual - b.prediction).abs()
    b["sq_error"] = (b.actual - b.prediction) ** 2
    b["ape"] = np.where(b.actual.abs() > 1e-6, b.abs_error / b.actual.abs(), np.nan)
    return b.groupby(["horizon_weeks", "model"], as_index=False).agg(MAE=("abs_error", "mean"), RMSE=("sq_error", lambda x: float(np.sqrt(x.mean()))), MAPE_pct=("ape", lambda x: 100 * x.mean()), n=("actual", "size"))


def forecast_table(data: PreparedData, horizon: int = 8, model: str = "Exponential smoothing") -> pd.DataFrame:
    y = data.weekly[CARE].dropna()
    dates = pd.date_range(y.index[-1] + pd.Timedelta(days=7), periods=horizon, freq="7D")
    predictions = forecast_one(y, horizon, model)
    sigma = float(y.diff().dropna().tail(52).std())
    sigma = max(sigma, 1.0 if np.isfinite(sigma) else 1.0)
    # Empirical weekly-change planning range widens with square-root horizon; it is not a calibrated interval.
    return pd.DataFrame({"Date": dates, "Forecast": predictions,
                         "Lower 90%": np.maximum(0, predictions - 1.645 * sigma * np.sqrt(np.arange(1, horizon + 1))),
                         "Upper 90%": predictions + 1.645 * sigma * np.sqrt(np.arange(1, horizon + 1)),
                         "Model": model})


def discharge_forecast(data: PreparedData, horizon: int = 8, model: str = "Exponential smoothing") -> pd.DataFrame:
    y = data.weekly[DISCHARGES].dropna()
    # Observed reporting-day mean scaled to a nominal 7-day week; assumes observed dates represent the week.
    values = forecast_one(y, horizon, model)
    sigma = float(y.diff().dropna().tail(52).std())
    sigma = max(sigma if np.isfinite(sigma) else 1.0, 1.0)
    return pd.DataFrame({"Date": pd.date_range(y.index[-1] + pd.Timedelta(days=7), periods=horizon, freq="7D"), "Forecast": values,
                         "Lower 90%": np.maximum(0, values - 1.645 * sigma * np.sqrt(np.arange(1, horizon + 1))),
                         "Upper 90%": values + 1.645 * sigma * np.sqrt(np.arange(1, horizon + 1)), "Model": model})
