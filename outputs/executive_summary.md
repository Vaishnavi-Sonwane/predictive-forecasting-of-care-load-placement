# Executive Summary

## Purpose

This prototype forecasts short-term HHS care load and reported discharges from the supplied UAC public dataset. It provides a transparent dashboard for planning conversations, not an official HHS projection.

## What the data say

- The supplied file has 720 valid reporting dates from 12 January 2023 to 21 December 2025; 450 blank rows were removed.
- Reports cover 67% of calendar dates, so flow estimates require a stated reporting-cadence assumption.
- In a rolling backtest across the latest 20 origins, damped exponential smoothing had care-load MAE of about 29 children at one week and 98 at four weeks.
- Discharges were less predictable: best one-week MAE was about 15 nominal weekly discharges; at three weeks the four-week average was best (MAE about 21), while persistence was marginally best at four weeks (MAE about 21).
- Random Forest and Gradient Boosting did not outperform the simpler benchmarks on this sample.

## Planning implications

Use the care-load forecast as a short-range planning signal and review the interval alongside live operational information. Treat the discharge forecast as a broader and less certain estimate. The dashboard compares model performance, lets the analyst change forecast horizon and model, provides an exploratory flow-pressure sensitivity, and exports forecast values.

The supplied extract ends 21 December 2025. HHS Data Hub showed a newer update dated 27 July 2026 when the project was prepared. Refresh the CSV before using the dashboard for current planning.

## What is still needed for capacity decisions

The dataset contains no open-bed capacity, staffing, pending referrals, sponsor-ready caseload, or placement-pipeline measures. Therefore this analysis cannot estimate capacity-breach probability, unsatisfied placement demand, or surge lead time. “Discharge demand” is a forecast of reported discharge flow, not a count of children waiting for placement.

## Recommended next steps

1. Refresh the public source and retain dated snapshots.
2. Add weekly staffed capacity and placement-pipeline inputs.
3. Monitor horizon-specific error against the persistence baseline.
4. Review forecasts and scenarios with program operations before staffing or placement decisions.

See the full [research paper](research_paper.md) and run instructions in the project README.
