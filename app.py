from __future__ import annotations

from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics import (
    CBP_LOAD_COL,
    DATE_COL,
    DISCHARGE_COL,
    HHS_LOAD_COL,
    INTAKE_COL,
    TRANSFER_COL,
    aggregate_metrics,
    compute_kpis,
    detect_stress_windows,
    load_time_series,
    prepare_daily_metrics,
    validate_data,
)


st.set_page_config(
    page_title="UAC Care Load Analytics",
    page_icon=None,
    layout="wide",
)

SAMPLE_PATH = Path("data/sample_uac_daily.csv")


@st.cache_data
def cached_load(source):
    return load_time_series(source)


def format_number(value: float) -> str:
    if value != value:
        return "N/A"
    return f"{value:,.0f}"


def format_percent(value: float) -> str:
    if value != value:
        return "N/A"
    return f"{value:.1%}"


st.title("System Capacity & Care Load Analytics")
st.caption("Operational monitoring framework for CBP-to-HHS care load, flow balance, backlog pressure, and strain windows.")

with st.sidebar:
    st.header("Controls")
    uploaded_file = st.file_uploader("Upload daily UAC CSV", type=["csv"])
    source = uploaded_file if uploaded_file else SAMPLE_PATH
    granularity = st.segmented_control("Time granularity", ["Daily", "Weekly", "Monthly"], default="Daily")
    show_rolling = st.toggle("Show rolling averages", value=True)
    show_stress = st.toggle("Highlight stress windows", value=True)
    st.info("Bundled sample data is synthetic. Upload official data for operational use.")

raw = cached_load(source)
validation = validate_data(raw)
daily = prepare_daily_metrics(raw)

min_date = daily[DATE_COL].min().date()
max_date = daily[DATE_COL].max().date()

with st.sidebar:
    selected_range = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

if isinstance(selected_range, tuple) and len(selected_range) == 2:
    start_date, end_date = selected_range
else:
    start_date, end_date = min_date, max_date

filtered_daily = daily[(daily[DATE_COL].dt.date >= start_date) & (daily[DATE_COL].dt.date <= end_date)]
display_data = aggregate_metrics(filtered_daily, granularity)
kpis = compute_kpis(filtered_daily)
stress_windows = detect_stress_windows(filtered_daily)

kpi_cols = st.columns(5)
kpi_cols[0].metric("Total Children Under Care", format_number(kpis["Total Children Under Care"]))
kpi_cols[1].metric("Net Intake Pressure", format_number(kpis["Net Intake Pressure"]))
kpi_cols[2].metric("Volatility Index", f"{kpis['Care Load Volatility Index']:.2f}%")
kpi_cols[3].metric("Backlog Accumulation", format_number(kpis["Backlog Accumulation Rate"]))
kpi_cols[4].metric("Discharge Offset", format_percent(kpis["Discharge Offset Ratio"]))

tab_overview, tab_flows, tab_quality, tab_table = st.tabs(
    ["System Load", "Flow Balance", "Data Quality", "Analytic Table"]
)

with tab_overview:
    left, right = st.columns([1.3, 1])

    with left:
        load_fig = go.Figure()
        load_fig.add_trace(
            go.Scatter(
                x=display_data[DATE_COL],
                y=display_data["Total System Load"],
                name="Total System Load",
                mode="lines",
                line=dict(color="#194A7A", width=3),
            )
        )
        if show_rolling and granularity == "Daily":
            load_fig.add_trace(
                go.Scatter(
                    x=display_data[DATE_COL],
                    y=display_data["7-day Total Load"],
                    name="7-day average",
                    mode="lines",
                    line=dict(color="#D55E00", width=2),
                )
            )
            load_fig.add_trace(
                go.Scatter(
                    x=display_data[DATE_COL],
                    y=display_data["14-day Total Load"],
                    name="14-day average",
                    mode="lines",
                    line=dict(color="#009E73", width=2, dash="dot"),
                )
            )
        if show_stress and not stress_windows.empty:
            for _, window in stress_windows.iterrows():
                load_fig.add_vrect(
                    x0=window["Start Date"],
                    x1=window["End Date"],
                    fillcolor="#E69F00",
                    opacity=0.14,
                    line_width=0,
                )
        load_fig.update_layout(
            title="Total Care System Load",
            xaxis_title=None,
            yaxis_title="Children",
            hovermode="x unified",
            legend_orientation="h",
            margin=dict(l=20, r=20, t=50, b=20),
        )
        st.plotly_chart(load_fig, use_container_width=True)

    with right:
        comparison = px.area(
            display_data,
            x=DATE_COL,
            y=[CBP_LOAD_COL, HHS_LOAD_COL],
            title="CBP vs HHS Active Load",
            labels={"value": "Children", "variable": "Metric"},
            color_discrete_sequence=["#6A4C93", "#2A9D8F"],
        )
        comparison.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(comparison, use_container_width=True)

with tab_flows:
    flow_left, flow_right = st.columns(2)
    with flow_left:
        flow_fig = px.line(
            display_data,
            x=DATE_COL,
            y=[INTAKE_COL, TRANSFER_COL, DISCHARGE_COL],
            title="Daily Operational Flows",
            labels={"value": "Children", "variable": "Flow"},
            color_discrete_sequence=["#0072B2", "#CC79A7", "#009E73"],
        )
        flow_fig.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(flow_fig, use_container_width=True)

    with flow_right:
        backlog_fig = go.Figure()
        backlog_fig.add_trace(
            go.Bar(
                x=display_data[DATE_COL],
                y=display_data["Net Daily Intake"],
                name="Net Daily Intake",
                marker_color="#C44536",
            )
        )
        backlog_fig.add_trace(
            go.Scatter(
                x=display_data[DATE_COL],
                y=display_data["Cumulative Backlog"],
                name="Cumulative Backlog",
                yaxis="y2",
                line=dict(color="#194A7A", width=3),
            )
        )
        backlog_fig.update_layout(
            title="Net Intake and Backlog Trend",
            yaxis=dict(title="Net Intake"),
            yaxis2=dict(title="Cumulative Backlog", overlaying="y", side="right"),
            hovermode="x unified",
            legend_orientation="h",
            margin=dict(l=20, r=20, t=50, b=20),
        )
        st.plotly_chart(backlog_fig, use_container_width=True)

    ratio_fig = px.line(
        display_data,
        x=DATE_COL,
        y="Discharge Offset Ratio",
        title="Discharge Offset Ratio",
        labels={"Discharge Offset Ratio": "Discharges / Transfers"},
        color_discrete_sequence=["#2A9D8F"],
    )
    ratio_fig.add_hline(y=1, line_dash="dash", line_color="#444", annotation_text="Balanced flow")
    ratio_fig.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(ratio_fig, use_container_width=True)

with tab_quality:
    quality_cols = st.columns(4)
    quality_cols[0].metric("Missing Columns", len(validation.missing_columns))
    quality_cols[1].metric("Duplicate Dates", validation.duplicate_dates)
    quality_cols[2].metric("Missing Dates", validation.missing_dates)
    quality_cols[3].metric("Anomaly Flags", validation.anomaly_count)

    st.subheader("Validation Notes")
    for note in validation.notes:
        st.write(f"- {note}")

    if stress_windows.empty:
        st.success("No prolonged strain windows detected for the selected period.")
    else:
        st.subheader("Detected Strain Windows")
        st.dataframe(stress_windows, use_container_width=True, hide_index=True)

with tab_table:
    st.dataframe(display_data, use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered analytics CSV",
        display_data.to_csv(index=False).encode("utf-8"),
        file_name="uac_capacity_analytics.csv",
        mime="text/csv",
    )
