from __future__ import annotations

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path


OUTPUT_PATH = Path("data/sample_uac_daily.csv")


def main() -> None:
    random.seed(42)
    start = date(2023, 1, 1)
    end = date(2025, 12, 31)
    days = (end - start).days + 1
    hhs_load = 9600.0
    rows = []

    for index in range(days):
        current = start + timedelta(days=index)
        seasonal = math.sin(2 * math.pi * index / 365.25)
        short_cycle = math.sin(2 * math.pi * index / 45)
        surge = math.exp(-((index - 470) ** 2) / (2 * 70**2))
        surge += 0.7 * math.exp(-((index - 860) ** 2) / (2 * 55**2))

        apprehended = max(120, 310 + 70 * seasonal + 35 * short_cycle + 130 * surge + random.gauss(0, 18))
        transfers = max(60, 0.72 * apprehended + 35 * surge + random.gauss(0, 14))
        discharges = 235 + 45 * math.sin(2 * math.pi * (index - 30) / 365.25)
        discharges += 20 * short_cycle + 55 * math.exp(-((index - 550) ** 2) / (2 * 95**2))
        discharges = max(70, discharges + random.gauss(0, 12))

        cbp_load = 850 + 1.25 * (apprehended - transfers) + 130 * surge + 70 * seasonal + random.gauss(0, 25)
        cbp_load = max(cbp_load, transfers + 20)
        hhs_load = max(3500, hhs_load + transfers - discharges + random.gauss(0, 8))

        rows.append(
            {
                "Date": current.isoformat(),
                "Children apprehended and placed in CBP custody": round(apprehended),
                "Children in CBP custody": round(cbp_load),
                "Children transferred out of CBP custody": round(transfers),
                "Children in HHS Care": round(hhs_load),
                "Children discharged from HHS Care": round(discharges),
            }
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
