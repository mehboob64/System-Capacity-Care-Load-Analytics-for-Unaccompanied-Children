# System Capacity & Care Load Analytics for Unaccompanied Children

This project provides a Streamlit analytics dashboard and written stakeholder deliverables for monitoring care-system load across CBP custody and HHS care.

The application computes operational metrics such as total system load, net intake pressure, backlog accumulation, rolling averages, discharge offset ratios, and stress windows. It is designed to work with daily time-series data for 2023-2025 using the project schema below.

## Expected Data Columns

| Column | Description |
| --- | --- |
| `Date` | Reporting date |
| `Children apprehended and placed in CBP custody` | Daily intake volume |
| `Children in CBP custody` | Active CBP care load |
| `Children transferred out of CBP custody` | Flow into HHS system |
| `Children in HHS Care` | Active HHS care load |
| `Children discharged from HHS Care` | Successful sponsor placements |

## Quick Start

1. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

2. Run the Streamlit dashboard:

   ```powershell
   streamlit run app.py
   ```

3. Upload an official CSV from the sidebar, or use the included synthetic sample data at `data/sample_uac_daily.csv`.

## Project Structure

| Path | Purpose |
| --- | --- |
| `app.py` | Streamlit dashboard |
| `src/analytics.py` | Data validation, feature engineering, KPIs, and stress detection |
| `data/sample_uac_daily.csv` | Synthetic demonstration data, not official federal data |
| `deliverables/research_paper.md` | Research-style EDA and methodology paper |
| `deliverables/executive_summary.md` | Concise stakeholder summary |

## Important Data Note

The bundled sample data is synthetic and exists only to demonstrate the analytics workflow. Replace it with official daily operational data before making policy, staffing, shelter, or healthcare delivery decisions.
