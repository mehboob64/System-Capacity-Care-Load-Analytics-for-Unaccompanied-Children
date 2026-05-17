# System Capacity & Care Load Analytics for Unaccompanied Children

## Abstract

The Unaccompanied Alien Children program operates as a dynamic care pipeline that starts with CBP custody and continues through HHS shelter, medical, psychological, welfare, and sponsor-placement processes. This project translates daily operational counts into a structured healthcare capacity analytics framework. The framework quantifies total system load, inflow-outflow balance, backlog accumulation, volatility, and strain periods so stakeholders can move from reactive monitoring toward evidence-based care delivery planning.

## Problem Context

HHS and partner agencies collect daily operational data, but raw counts alone do not provide a centralized view of care-system sustainability. The absence of structured analytics can obscure whether transfers into HHS care are being offset by discharges, whether high-load periods are temporary or prolonged, and whether operational stress is accumulating across the pipeline.

## Data Structure

The analysis expects daily observations from 2023-2025 with six fields:

- Reporting date.
- Children apprehended and placed in CBP custody.
- Children in CBP custody.
- Children transferred out of CBP custody.
- Children in HHS care.
- Children discharged from HHS care.

The included demonstration dataset is synthetic and should be replaced with official operational data for decision-making.

## Methodology

The analytical workflow begins with data ingestion, type conversion, chronological ordering, duplicate-date detection, and construction of a complete daily index. Missing daily values are interpolated for continuity in dashboard views, while data-quality warnings remain visible to preserve transparency.

Logical validation checks flag cases where transfers exceed reported CBP custody, discharges exceed reported HHS care, duplicate reporting dates exist, dates are missing, or negative values appear in count fields.

Derived metrics include:

- Total System Load = CBP custody + HHS care.
- Net Daily Intake = transfers into HHS - discharges from HHS.
- Care Load Growth Rate = day-over-day percent change in total system load.
- Cumulative Backlog = cumulative sum of net daily intake.
- Discharge Offset Ratio = HHS discharges divided by transfers from CBP.
- Care Load Volatility = rolling 14-day standard deviation of total system load.

## Key Performance Indicators

Total Children Under Care represents the latest system-wide responsibility. Net Intake Pressure captures the recent average gap between inflow and outflow. The Care Load Volatility Index measures short-term instability. Backlog Accumulation Rate focuses on sustained positive net intake. Discharge Offset Ratio assesses whether sponsor placements are relieving inflow pressure.

## Stress Identification

The dashboard assigns a composite stress score using normalized load, positive net intake pressure, volatility, and discharge-offset gaps. Prolonged strain windows are detected when stress remains elevated or when net intake stays positive for a sustained period. These windows help identify periods when staffing, shelter capacity, case management, and healthcare services may need closer review.

## Expected Insights

With official data, the framework can identify periods when total system load peaks, when HHS care load grows faster than discharge capacity, and when discharge rates offset transfers sufficiently to create relief. It can also compare daily, weekly, and monthly trends to distinguish short disruptions from structural pressure.

## Policy and Operational Recommendations

Agencies should monitor net intake pressure alongside total load because a stable census can mask emerging flow imbalance. Stress windows should trigger review of staffing, medical screening capacity, sponsor-vetting throughput, and bed availability. Data-quality flags should be part of regular operational reporting so anomalous data does not distort policy interpretation.

## Limitations

This framework depends on accurate daily reporting and does not include individual-level case complexity, facility-level capacity, regional variation, age group, medical acuity, or sponsor-vetting bottleneck details. Those dimensions should be integrated when available.

## Conclusion

The project provides a policy-aligned healthcare analytics framework for monitoring system load, care-flow balance, and operational strain in the UAC care pipeline. By turning daily counts into interpretable metrics and dashboards, it supports more timely, transparent, and data-driven humanitarian response planning.
