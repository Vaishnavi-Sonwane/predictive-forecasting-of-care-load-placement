# Predictive Forecasting of Care Load & Placement Demand

## Abstract

This study builds a short-horizon forecasting prototype for weekly children in HHS care and reported discharges using the supplied HHS Unaccompanied Alien Children Program extract. It compares persistence, a four-week moving average, damped exponential smoothing, Random Forest, and Gradient Boosting using rolling-origin forecasts. The 720 valid reports span 12 January 2023–21 December 2025. Because the file has intermittent reporting dates and no capacity or placement-pipeline measures, flow forecasts are interpreted as nominal weekly rates and the results are planning estimates rather than operational capacity predictions. On the most recent 20 forecast origins, exponential smoothing had the lowest care-load error at every evaluated horizon: MAE rose from about 34 children at one week to 105 at four weeks. Discharge-flow estimates were noisier: exponential smoothing led at one week (MAE about 15 per nominal week), while a four-week average performed best at four weeks (MAE about 22). The machine-learning models did not improve on these simple statistical baselines in this small, regime-shifting sample.

## 1. Introduction

Care organizations need to anticipate changes in caseload, transfer flow, and sponsor placement volume. This project tests whether the public daily reporting series supports short-term forecasts that can help frame planning discussions. The HHS Data Hub describes the dataset as reporting children in HHS care and children discharged, alongside CBP apprehensions, CBP custody, and transfers. HHS describes ORR care as following referral by another federal agency and ending for most children when placed with a sponsor. [HHS Data Hub dataset page](https://datahub.hhs.gov/National/HHS-Unaccompanied-Alien-Children-Program/ehpz-xc9n); [HHS Unaccompanied Children Information](https://www.hhs.gov/programs/social-services/unaccompanied-children/index.html)

The project questions are: (1) what short-term forecast can be made for the reported HHS care stock; (2) how well can reported discharge volume be forecast; and (3) what operating risks cannot be inferred from this dataset?

## 2. Data and preparation

The supplied CSV contains 1,170 physical rows, of which 450 are fully blank and 720 contain valid, dated observations. The valid observations span 1,075 calendar days from 12 January 2023 through 21 December 2025, with reporting-date coverage of 67.0%. The median interval between reports is one day and the maximum is ten days. The supplied extract is therefore not a complete daily panel. The HHS Data Hub page currently reports a newer dataset update (27 July 2026); this analysis intentionally preserves and evaluates the user-supplied historical extract rather than silently replacing it.

Duplicate dates, if present, are reduced to the last record. HHS care is a stock and is represented by the last reported value in each Sunday-ending week. A single missing weekly stock observation may be linearly interpolated; longer gaps are left unavailable. In this source every week in the usable span has a stock observation, so no interpolation was needed. Weekly flow series are constructed as the mean reported value in a week multiplied by seven. This produces a nominal seven-day estimate only under the assumption that observed report dates represent the week. Changes in reporting cadence or systematic differences between reported and unreported days can bias the estimate.

The flow pressure indicator is transfers out of CBP custody minus HHS discharges, each expressed as a nominal-week rate. It is a descriptive pressure signal and is not treated as a stock accounting identity: timing, referral, and other program flows are not fully represented in this file.

## 3. Methods

### Forecast targets

The first target is weekly HHS care stock. The second is nominal-week HHS discharge flow, derived from observations as described above. “Discharge demand” in this analysis means expected reported discharge volume. It does not mean the number of children awaiting placement, the number of beds released, or the number of sponsor-ready cases.

### Models

- **Persistence:** the latest observed weekly value is carried forward.
- **Four-week average:** the latest four observations' average is carried forward.
- **Damped exponential smoothing:** level and trend are updated using a small grid of smoothing parameters; trend is damped for multi-step forecasts.
- **Random Forest:** recursive one-to-four-week forecasts from lagged values, rolling means and variability, and annual calendar terms.
- **Gradient Boosting:** the same lag and calendar inputs using a Huber-loss gradient boosting regressor.

Feature availability at forecast time is respected. The tree models are univariate target-history models; transfer and discharge pressure is shown as a descriptive signal and sensitivity input rather than as a future-known model feature. This avoids leaking unavailable future flows into a forecast.

### Evaluation

The evaluation uses a chronological rolling-origin procedure, with the model refit at each of the most recent 20 origins and forecasts scored at one, two, three, and four weeks. No random split is used. Metrics are MAE, RMSE, and MAPE. Weekly discharge series can contain zero values, so MAPE is a fragile measure and should be read with MAE/RMSE. The displayed planning band uses historical weekly-change volatility and a square-root horizon widening rule; it is an approximate 90% band, not a calibrated probabilistic interval.

## 4. Results

### Care-load model comparison

| Horizon | Best model | MAE (children) | RMSE (children) | MAPE |
|---|---|---:|---:|---:|
| 1 week | Exponential smoothing | 29 | 36 | 1.4% |
| 2 weeks | Exponential smoothing | 50 | 60 | 2.3% |
| 3 weeks | Exponential smoothing | 73 | 85 | 3.3% |
| 4 weeks | Exponential smoothing | 98 | 110 | 4.4% |

Tree models performed materially worse than persistence or smoothing at each horizon. This is consistent with the limited weekly sample and the recent large shift in the care-load level: the most recent observations are much lower than the long-run sample average. Long-run average forecasts would lag this change. The result supports starting with a simple smoothing model and keeping benchmark comparison visible, rather than assuming that model complexity improves forecasts.

### Discharge-flow model comparison

| Horizon | Best model | MAE (nominal weekly discharges) | RMSE | MAPE |
|---|---|---:|---:|---:|
| 1 week | Exponential smoothing | 15 | 20 | 18.2% |
| 2 weeks | Exponential smoothing | 19 | 26 | 24.1% |
| 3 weeks | Four-week average | 21 | 27 | 28.2% |
| 4 weeks | Persistence | 21 | 26 | 27.1% |

Discharge-flow forecasts are less reliable in relative terms than care-stock forecasts. At three weeks the four-week average is marginally best by MAE; by four weeks persistence is marginally better. Differences among simple models are small compared with flow uncertainty. The report-date scaling assumption also adds uncertainty not captured by the model error metrics.

### Current-from-extract illustrative forecast

Using exponential smoothing at the final available source week (ending 21 December 2025), the model projects roughly 2,494 children in care one week later and 2,536 at eight weeks. The nominal weekly discharge-flow point forecast is roughly 72. These are historical-extract illustrations only. They are not current November 2026 forecasts and should not be used for present operational decisions without a refreshed data file and fresh backtesting.

## 5. Operational interpretation

The care-load series is forecastable over one to four weeks in the recent backtest with lower absolute error than the discharge flow. Forecasts should be used as a planning range and reviewed against current referrals, facility placement, sponsor readiness, and staffing information. The dashboard lets an analyst change the horizon and model, view the uncertainty band, compare the scenarios, inspect rolling-origin results, and download the forecast table.

The scenario selector applies a ±20% sensitivity to recent transfer-minus-discharge net pressure. It is a simple exploratory adjustment, not a causal model and not a policy forecast. Since the available data do not include bed capacity or pending placement counts, it cannot support a defensible probability of capacity breach or surge lead-time KPI. Forecast accuracy is reported directly through historical MAE/RMSE/MAPE rather than collapsed into a potentially misleading single “accuracy percentage.”

## 6. Limitations and safeguards

1. **Stale source extract:** the supplied data end 21 December 2025. The HHS Data Hub listed an update dated 27 July 2026 when reviewed.
2. **Incomplete daily cadence:** only 67.0% of calendar dates in the span are represented. The flow scaling assumption may be biased.
3. **Regime changes:** large changes in the level of care can make older observations less informative; models are refit but not given policy covariates.
4. **No operational capacity variables:** no licensed beds, open beds, staffing levels, pending referrals, pending sponsor placements, or facility mix are supplied.
5. **Aggregate-only data:** forecasts cannot identify subgroup needs, clinical acuity, or individual outcomes.
6. **Uncertainty band:** the current band is a simple empirical volatility band and must not be interpreted as a calibrated risk probability.

## 7. Recommendations

- Refresh the input directly from the HHS Data Hub before every planning run and retain a dated source snapshot.
- Add validated weekly measures for open and staffed capacity, incoming referrals awaiting placement, sponsor-ready cases, and placement pipeline stage.
- Monitor forecast error by horizon and data vintage; benchmark each candidate model against persistence.
- Investigate reporting-cadence changes before relying on weekly flow normalization.
- Use a scenario review with program operations, medical, case management, and placement teams; keep a human decision maker accountable for deployment decisions.
- Once sufficient capacity history is available, build a separate capacity-risk model and calibrate breach probabilities on held-out periods.

## 8. Conclusion

The supplied series supports a reproducible short-term forecast of weekly HHS care load, with damped exponential smoothing outperforming the tested tree models and simple baselines in the latest rolling-origin comparison. Discharge flow is harder to predict, especially beyond one week. This prototype provides a useful forecasting foundation and a transparent dashboard, while making clear that current capacity stress, placement backlog, and surge timing require additional operational data.
