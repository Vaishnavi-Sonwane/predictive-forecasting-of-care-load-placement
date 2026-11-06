# Submission Video Notes

## Project explanation walkthrough

Target length: about 2 minutes. Replace any bracketed parts only with accurate details.

> Hello, I’m [your name]. This project forecasts short-term HHS care load and discharge volumes from the public Unaccompanied Alien Children Program dataset.
>
> The dashboard lets a user choose a forecast horizon and model, compare model errors, view an approximate uncertainty band, explore a simple net-flow sensitivity, and download forecast results.
>
> The analysis compares persistence and a four-week average with damped exponential smoothing, Random Forest, and Gradient Boosting. I evaluated them with rolling-origin forecasts instead of a random split. In the supplied extract, exponential smoothing had the lowest care-load error in the latest backtest; discharge flow was harder to forecast, and simple baselines were competitive.
>
> The source is not a complete daily record, so the project aggregates to weeks and labels its assumptions. The supplied extract ends on 21 December 2025. It also does not include open capacity, pending referrals, staffing, or the placement pipeline. For that reason, the dashboard cannot estimate a real capacity-breach probability or children waiting for placement. Those measures would need additional operational data.
>
> The project files and setup instructions are available at `https://github.com/Vaishnavi-Sonwane/predictive-forecasting-of-care-load-placement`. The research paper is at `https://github.com/Vaishnavi-Sonwane/predictive-forecasting-of-care-load-placement/blob/main/outputs/research_paper.md`. The live dashboard is at `https://uac-care-load-forecast.streamlit.app/`.

Suggested on-screen sequence: show the dashboard settings, care-load chart, discharge estimate, model comparison, data-quality tab, and CSV download control. Use a refreshed dataset for the recording if available.

## Internship experience and feedback video

This section is a prompt, not a script of personal claims. Fill it with your own experience and opinions before recording.

- My role or program was: [your actual role/program].
- The dates or period were: [actual period].
- The project I completed was: [brief accurate description].
- Skills or tools I learned: [your own examples].
- A challenge I worked through: [your own example].
- What helped me during the internship: [your honest feedback].
- One improvement I would suggest: [your constructive feedback].
- My overall takeaway: [your own conclusion].

Close by thanking the program only if that reflects your experience. Do not include private details about other people or cases.
