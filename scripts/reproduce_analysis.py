"""Recreate the report's rolling-origin score table and illustrative forecasts."""
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.forecasting import (
    CARE, DISCHARGES, load_data, walk_forward, score_forecasts,
    forecast_table, discharge_forecast,
)

DATA = ROOT / "data" / "HHS_Unaccompanied_Alien_Children_Program.csv"
OUT = ROOT / "outputs"


def main() -> None:
    data = load_data(str(DATA))
    scores = []
    for target, target_name in ((CARE, "care_load"), (DISCHARGES, "discharge_flow")):
        scored = score_forecasts(walk_forward(data.weekly[target], max_horizon=4, folds=20))
        scored.insert(0, "target", target_name)
        scores.append(scored)
    pd.concat(scores, ignore_index=True).to_csv(OUT / "model_comparison.csv", index=False)
    care = forecast_table(data, horizon=8, model="Exponential smoothing")
    flow = discharge_forecast(data, horizon=8, model="Exponential smoothing")
    care["Discharge demand estimate"] = flow["Forecast"].to_numpy()
    care.to_csv(OUT / "illustrative_forecast_from_supplied_extract.csv", index=False)
    print(f"Wrote evaluation and illustrative forecast to {OUT}")


if __name__ == "__main__":
    main()
