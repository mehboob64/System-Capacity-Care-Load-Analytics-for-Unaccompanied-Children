from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


DATE_COL = "Date"
INTAKE_COL = "Children apprehended and placed in CBP custody"
CBP_LOAD_COL = "Children in CBP custody"
TRANSFER_COL = "Children transferred out of CBP custody"
HHS_LOAD_COL = "Children in HHS Care"
DISCHARGE_COL = "Children discharged from HHS Care"

REQUIRED_COLUMNS = [
    DATE_COL,
    INTAKE_COL,
    CBP_LOAD_COL,
    TRANSFER_COL,
    HHS_LOAD_COL,
    DISCHARGE_COL,
]


@dataclass(frozen=True)
class ValidationResult:
    missing_columns: list[str]
    duplicate_dates: int
    missing_dates: int
    anomaly_count: int
    notes: list[str]


def load_time_series(source) -> pd.DataFrame:
    data = pd.read_csv(source)
    missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    data = data[REQUIRED_COLUMNS].copy()
    data[DATE_COL] = pd.to_datetime(data[DATE_COL], errors="coerce")
    data = data.dropna(subset=[DATE_COL])

    numeric_columns = [column for column in REQUIRED_COLUMNS if column != DATE_COL]
    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.sort_values(DATE_COL).reset_index(drop=True)
    return data


def validate_data(data: pd.DataFrame) -> ValidationResult:
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    notes: list[str] = []

    if missing_columns:
        return ValidationResult(missing_columns, 0, 0, 0, ["Schema validation failed."])

    duplicate_dates = int(data[DATE_COL].duplicated().sum())
    full_index = pd.date_range(data[DATE_COL].min(), data[DATE_COL].max(), freq="D")
    missing_dates = int(len(full_index.difference(pd.DatetimeIndex(data[DATE_COL]))))

    transfer_anomalies = data[TRANSFER_COL] > data[CBP_LOAD_COL]
    discharge_anomalies = data[DISCHARGE_COL] > data[HHS_LOAD_COL]
    negative_values = data[[INTAKE_COL, CBP_LOAD_COL, TRANSFER_COL, HHS_LOAD_COL, DISCHARGE_COL]] < 0
    anomaly_count = int(transfer_anomalies.sum() + discharge_anomalies.sum() + negative_values.sum().sum())

    if duplicate_dates:
        notes.append(f"{duplicate_dates} duplicated reporting date(s) detected.")
    if missing_dates:
        notes.append(f"{missing_dates} missing daily reporting date(s) detected.")
    if int(transfer_anomalies.sum()):
        notes.append("Some transfer counts exceed reported CBP custody load.")
    if int(discharge_anomalies.sum()):
        notes.append("Some discharge counts exceed reported HHS care load.")
    if int(negative_values.sum().sum()):
        notes.append("Negative count values were detected.")
    if not notes:
        notes.append("No structural validation issues detected.")

    return ValidationResult(missing_columns, duplicate_dates, missing_dates, anomaly_count, notes)


def prepare_daily_metrics(data: pd.DataFrame) -> pd.DataFrame:
    prepared = data.copy()
    prepared = prepared.drop_duplicates(subset=[DATE_COL], keep="last")
    prepared = prepared.set_index(DATE_COL).sort_index()

    complete_index = pd.date_range(prepared.index.min(), prepared.index.max(), freq="D")
    prepared = prepared.reindex(complete_index)
    prepared.index.name = DATE_COL

    count_columns = [INTAKE_COL, CBP_LOAD_COL, TRANSFER_COL, HHS_LOAD_COL, DISCHARGE_COL]
    prepared[count_columns] = prepared[count_columns].interpolate(method="time").ffill().bfill()

    prepared["Total System Load"] = prepared[CBP_LOAD_COL] + prepared[HHS_LOAD_COL]
    prepared["Net Daily Intake"] = prepared[TRANSFER_COL] - prepared[DISCHARGE_COL]
    prepared["Care Load Growth Rate"] = prepared["Total System Load"].pct_change().replace([np.inf, -np.inf], np.nan)
    prepared["Care Load Growth Rate"] = prepared["Care Load Growth Rate"].fillna(0.0)
    prepared["Cumulative Backlog"] = prepared["Net Daily Intake"].cumsum()
    prepared["Discharge Offset Ratio"] = np.where(
        prepared[TRANSFER_COL] > 0,
        prepared[DISCHARGE_COL] / prepared[TRANSFER_COL],
        np.nan,
    )
    prepared["Care Load Volatility"] = prepared["Total System Load"].rolling(14, min_periods=3).std()
    prepared["7-day Total Load"] = prepared["Total System Load"].rolling(7, min_periods=1).mean()
    prepared["14-day Total Load"] = prepared["Total System Load"].rolling(14, min_periods=1).mean()
    prepared["7-day Net Intake"] = prepared["Net Daily Intake"].rolling(7, min_periods=1).mean()
    prepared["Positive Net Intake"] = prepared["Net Daily Intake"] > 0
    prepared["Backlog Indicator"] = (
        prepared["Positive Net Intake"].rolling(7, min_periods=7).sum().fillna(0).ge(7)
    )
    prepared["Stress Score"] = _stress_score(prepared)

    return prepared.reset_index()


def aggregate_metrics(data: pd.DataFrame, granularity: str) -> pd.DataFrame:
    if granularity == "Daily":
        return data.copy()

    rule = {"Weekly": "W-MON", "Monthly": "MS"}[granularity]
    metric_columns = [
        INTAKE_COL,
        CBP_LOAD_COL,
        TRANSFER_COL,
        HHS_LOAD_COL,
        DISCHARGE_COL,
        "Total System Load",
        "Net Daily Intake",
        "Cumulative Backlog",
        "7-day Total Load",
        "14-day Total Load",
        "7-day Net Intake",
        "Care Load Volatility",
        "Stress Score",
    ]
    aggregated = (
        data.set_index(DATE_COL)[metric_columns]
        .resample(rule)
        .mean()
        .round(2)
        .reset_index()
    )
    aggregated["Care Load Growth Rate"] = aggregated["Total System Load"].pct_change().fillna(0.0)
    aggregated["Discharge Offset Ratio"] = np.where(
        aggregated[TRANSFER_COL] > 0,
        aggregated[DISCHARGE_COL] / aggregated[TRANSFER_COL],
        np.nan,
    )
    aggregated["Backlog Indicator"] = aggregated["Net Daily Intake"] > 0
    return aggregated


def compute_kpis(data: pd.DataFrame) -> dict[str, float]:
    latest = data.iloc[-1]
    return {
        "Total Children Under Care": float(latest["Total System Load"]),
        "Net Intake Pressure": float(data["Net Daily Intake"].tail(7).mean()),
        "Care Load Volatility Index": float(data["Total System Load"].pct_change().tail(14).std(skipna=True) * 100),
        "Backlog Accumulation Rate": float(data["Net Daily Intake"].tail(14).clip(lower=0).mean()),
        "Discharge Offset Ratio": float(data["Discharge Offset Ratio"].tail(14).mean(skipna=True)),
    }


def detect_stress_windows(data: pd.DataFrame, minimum_days: int = 7) -> pd.DataFrame:
    threshold = data["Stress Score"].quantile(0.75)
    stressed = (data["Stress Score"] >= threshold) | data["Backlog Indicator"]
    windows = _contiguous_windows(data[DATE_COL], stressed, minimum_days)
    return pd.DataFrame(windows, columns=["Start Date", "End Date", "Days"])


def _stress_score(data: pd.DataFrame) -> pd.Series:
    load = _minmax(data["Total System Load"])
    net_pressure = _minmax(data["7-day Net Intake"].clip(lower=0))
    volatility = _minmax(data["Care Load Volatility"].fillna(0))
    offset_gap = (1 - data["Discharge Offset Ratio"]).clip(lower=0).fillna(0)
    offset_gap = _minmax(offset_gap)
    return (0.45 * load) + (0.25 * net_pressure) + (0.2 * volatility) + (0.1 * offset_gap)


def _minmax(series: pd.Series) -> pd.Series:
    minimum = series.min(skipna=True)
    maximum = series.max(skipna=True)
    if pd.isna(minimum) or pd.isna(maximum) or maximum == minimum:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - minimum) / (maximum - minimum)


def _contiguous_windows(dates: Iterable[pd.Timestamp], flags: Iterable[bool], minimum_days: int) -> list[tuple[pd.Timestamp, pd.Timestamp, int]]:
    windows: list[tuple[pd.Timestamp, pd.Timestamp, int]] = []
    start = None
    end = None
    length = 0

    for date, flag in zip(dates, flags):
        if flag:
            start = date if start is None else start
            end = date
            length += 1
        else:
            if start is not None and length >= minimum_days:
                windows.append((start, end, length))
            start = None
            end = None
            length = 0

    if start is not None and length >= minimum_days:
        windows.append((start, end, length))

    return windows
