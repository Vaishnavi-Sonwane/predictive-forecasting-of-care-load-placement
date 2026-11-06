from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.forecasting import CARE, DISCHARGES, MODEL_NAMES, load_data, walk_forward, score_forecasts, forecast_table, discharge_forecast

ROOT = Path(__file__).parent
DEFAULT_DATA = ROOT / "data" / "HHS_Unaccompanied_Alien_Children_Program.csv"
st.set_page_config(page_title="UAC Care Load Forecast", page_icon="📈", layout="wide")
st.title("UAC Care Load & Placement Demand Forecast")
st.caption("Planning support using weekly HHS public reporting data. Forecasts are directional estimates, not official HHS projections.")

with st.sidebar:
    st.header("Forecast settings")
    uploaded = st.file_uploader("Upload refreshed HHS CSV", type=["csv"])
    horizon = st.slider("Forecast horizon (weeks)", 1, 12, 8)
    model = st.selectbox("Forecast model", MODEL_NAMES, index=2)
    scenario = st.selectbox("Recent net-flow pressure", ["Central", "Lower pressure", "Higher pressure"], index=0)

@st.cache_data(show_spinner="Preparing weekly series…")
def prepare(file_bytes: bytes | None, path: str):
    if file_bytes is None:
        return load_data(path)
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        f.write(file_bytes)
        temp = f.name
    try:
        return load_data(temp)
    finally:
        Path(temp).unlink(missing_ok=True)

@st.cache_data(show_spinner="Running rolling-origin backtest…")
def model_scores(series: pd.Series):
    return score_forecasts(walk_forward(series, 4, 20))

try:
    data = prepare(uploaded.getvalue() if uploaded else None, str(DEFAULT_DATA))
except Exception as exc:
    st.error(f"Could not load the dataset: {exc}")
    st.stop()

q = data.quality
hub_update = pd.Timestamp("2026-07-27")
if q["end"] < hub_update:
    st.warning(f"Dataset ends {q['end']:%d %b %Y}. The HHS Data Hub listing was updated 27 Jul 2026, after this extract; upload a refreshed CSV before operational planning. This extract contains {q['observations']:,} dated rows over {q['calendar_days']:,} calendar days ({q['reporting_coverage_pct']:.1f}% reporting-date coverage). Unreported days are not assumed to be zero.")
else:
    st.info(f"Loaded {q['observations']:,} dated reports through {q['end']:%d %b %Y}, covering {q['reporting_coverage_pct']:.1f}% of calendar dates in the file. Unreported days are not assumed to be zero.")
history = data.weekly
care = forecast_table(data, horizon, model)
discharge = discharge_forecast(data, horizon, model)
recent_pressure = float(history["net_pressure"].tail(4).mean())
factor = {"Central": 0.0, "Lower pressure": -0.2, "Higher pressure": 0.2}[scenario]
adjustment = abs(recent_pressure) * factor * pd.Series(range(1, horizon + 1), index=care.index)
care["Scenario forecast"] = (care.Forecast + adjustment).clip(lower=0)

last_care = float(history[CARE].dropna().iloc[-1])
end_care = float(care["Scenario forecast"].iloc[-1])
c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest reported care load", f"{last_care:,.0f}", help=f"Last source report: {q['end']:%d %b %Y}")
c2.metric(f"Care load in {horizon} weeks", f"{end_care:,.0f}", f"{end_care-last_care:+,.0f} vs latest")
c3.metric("Projected weekly discharges", f"{discharge.Forecast.iloc[-1]:,.0f}", help="Observed reporting-day average scaled to a nominal 7-day week.")
c4.metric("Recent net flow pressure", f"{recent_pressure:+,.0f}/week", help="Estimated transfers minus discharges, each scaled from observed reporting dates.")

left, right = st.columns([1.7, 1])
with left:
    fig = go.Figure()
    hist = history[CARE].dropna()
    fig.add_trace(go.Scatter(x=hist.index, y=hist.values, name="Weekly care load", line=dict(color="#1F4E79", width=2)))
    fig.add_trace(go.Scatter(x=care.Date, y=care["Upper 90%"], name="Upper 90% planning band", line=dict(width=0)))
    fig.add_trace(go.Scatter(x=care.Date, y=care["Lower 90%"], name="Lower 90% planning band", fill="tonexty", fillcolor="rgba(75,145,195,.2)", line=dict(width=0)))
    fig.add_trace(go.Scatter(x=care.Date, y=care["Scenario forecast"], name=f"{model} — {scenario}", line=dict(color="#E07A1F", width=3, dash="dash")))
    fig.update_layout(title="Weekly children in HHS care", yaxis_title="Children", xaxis_title="Week ending", hovermode="x unified", legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(fig, use_container_width=True)
with right:
    dfig = go.Figure()
    dfig.add_trace(go.Scatter(x=discharge.Date, y=discharge["Upper 90%"], line=dict(width=0), showlegend=False))
    dfig.add_trace(go.Scatter(x=discharge.Date, y=discharge["Lower 90%"], fill="tonexty", fillcolor="rgba(80,170,125,.18)", line=dict(width=0), name="90% planning band"))
    dfig.add_trace(go.Bar(x=discharge.Date, y=discharge.Forecast, name="Estimated weekly discharge demand", marker_color="#4A9B72"))
    dfig.update_layout(title="Discharge demand estimate", yaxis_title="Discharges per nominal week", xaxis_title="Week ending")
    st.plotly_chart(dfig, use_container_width=True)
    st.caption("Flow values are normalized from observed reporting dates; estimates assume those dates represent the full week.")

st.subheader("Model comparison")
with st.spinner("Running rolling-origin backtest…"):
    care_scores = model_scores(history[CARE])
    discharge_scores = model_scores(history[DISCHARGES])
tab1, tab2, tab3 = st.tabs(["Care load", "Discharges", "Data quality"])
with tab1:
    st.caption("Rolling-origin evaluation on the most recent 20 origins, up to four weeks ahead. Lower MAE/RMSE is better.")
    st.dataframe(care_scores, hide_index=True, use_container_width=True)
with tab2:
    st.caption("Discharge target is the nominal-week rate estimate derived from observed report days.")
    st.dataframe(discharge_scores, hide_index=True, use_container_width=True)
with tab3:
    st.dataframe(pd.DataFrame([{"Check": k.replace("_", " ").title(), "Value": str(v)} for k, v in q.items()]), hide_index=True, use_container_width=True)
    st.info(f"The care-load history interpolates only isolated one-week gaps ({q['weeks_interpolated']} week(s)). Longer gaps are excluded. Flow estimates scale observed reporting-date averages to seven days. These assumptions can bias demand estimates if reporting cadence changes.")

st.subheader("Forecast table")
out = care[["Date", "Forecast", "Lower 90%", "Upper 90%", "Scenario forecast"]].merge(discharge[["Date", "Forecast"]].rename(columns={"Forecast": "Discharge demand estimate"}), on="Date")
display_out = out.copy()
for column in display_out.select_dtypes(include="number").columns:
    display_out[column] = display_out[column].round(0)
st.dataframe(display_out, hide_index=True, use_container_width=True)
st.download_button("Download forecast CSV", out.to_csv(index=False).encode("utf-8"), file_name="uac_forecast.csv", mime="text/csv")
st.caption("The approximate 90% planning band uses recent weekly-change volatility and widens with horizon; it is not a calibrated probability of capacity breach. The dataset lacks facility capacity, referrals pending, staffing, and placement pipeline data.")
