# Predictive Forecasting of Care Load & Placement Demand

A reproducible decision-support prototype for exploring short-term UAC care-load and discharge-demand forecasts from the HHS public reporting series.

## Included

- `app.py`: Streamlit dashboard with horizon and model selection, scenario sensitivity, forecast intervals, model comparison, data-quality view, and CSV download.
- `src/forecasting.py`: source cleaning, weekly preparation, baselines, damped exponential smoothing, Random Forest and Gradient Boosting models, and walk-forward metrics.
- `data/HHS_Unaccompanied_Alien_Children_Program.csv`: supplied source extract, preserved unchanged.
- `outputs/research_paper.md` and `outputs/executive_summary.md`: project write-ups.
- `outputs/model_comparison.csv`: 20-origin walk-forward scores by target and horizon.
- `outputs/illustrative_forecast_from_supplied_extract.csv`: forecast generated from the supplied extract, anchored at its final week (21 Dec 2025).

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Upload a refreshed CSV from the HHS Data Hub in the sidebar when one is available. The supplied extract ends 21 Dec 2025; the HHS Data Hub listing has since been updated.

## Data and targets

The input has one row per reporting date, not one row per calendar day. Blank lines are removed; duplicate dates keep the last row. HHS care is treated as a stock snapshot and resampled to the last observation in each Sunday-ending week. At most one isolated missing weekly stock point is interpolated. Flow fields are converted to nominal-week rates by multiplying the mean observed reporting-date value by seven. This assumes observed dates represent the week and can be biased when reporting cadence changes.

“Discharge demand” means a forecast of the source's discharge flow, not unsatisfied placement demand or beds released. The dataset does not include capacity, referrals pending, facility utilization, staffing, or placement pipeline data; therefore capacity-breach probability and surge lead time cannot be estimated responsibly from this file alone.

## Validation

The model table uses rolling-origin forecasts across the most recent 20 origins, evaluated at 1–4 weeks with MAE, RMSE and MAPE. Baselines are persistence and a trailing four-week average. Statistical and machine-learning comparisons use a damped exponential smoother, Random Forest and Gradient Boosting with lag, rolling and annual calendar features. All transformations use information available at each forecast origin. The approximate 90% band uses recent weekly-change volatility and widens with forecast horizon; it is not a calibrated probabilistic guarantee.

Recreate the evaluation CSV and the illustrative forecast with `python scripts/reproduce_analysis.py`. The forecast file is anchored to the supplied data's last week and is historical once that data becomes stale.

## Sources

- HHS Data Hub, [HHS Unaccompanied Alien Children Program](https://datahub.hhs.gov/National/HHS-Unaccompanied-Alien-Children-Program/ehpz-xc9n)
- HHS, [Unaccompanied Children Information](https://www.hhs.gov/programs/social-services/unaccompanied-children/index.html)

This is a prototype for analyst review. Refresh data, inspect coverage and forecast errors, review assumptions with program staff, and pair forecasts with validated operational capacity and referral-pipeline data before using forecasts for staffing or placement decisions.
