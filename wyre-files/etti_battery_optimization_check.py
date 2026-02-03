#!/usr/bin/env python3
"""Battery-need check for Mr Durosinmi Etti (client_id=4).

Uses exported CSVs in wyre-files/output/etti_solar_telemetry.
Goal: determine whether MORE battery capacity would likely reduce grid/gen usage
or just add cost (no more panel space).

Read-only local analysis.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from datetime import date, datetime, timedelta

BASE = "wyre-files/output/etti_solar_telemetry"
LAST_N_DAYS = 30


def _parse_day(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _percentile(sorted_vals, p: float) -> float:
    if not sorted_vals:
        return float("nan")
    k = (len(sorted_vals) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(sorted_vals[int(k)])
    return float(sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f))


def summarize(label: str, vals: list[float]) -> None:
    vals = [v for v in vals if v is not None]
    if not vals:
        print(label + ": no data")
        return
    vals.sort()
    avg = sum(vals) / len(vals)
    print(
        f"{label}: n={len(vals)} avg={avg:.2f} p50={_percentile(vals,0.5):.2f} p90={_percentile(vals,0.9):.2f} max={vals[-1]:.2f}"
    )


def main() -> None:
    # --- station capacity ---
    with open(f"{BASE}/station.csv") as f:
        r = list(csv.DictReader(f))
    if r:
        st = r[0]
        print("Installed station (from main_station):")
        print(
            f" - installed_capacity={st.get('installed_capacity')} | installed_battery_capacity={st.get('installed_battery_capacity')} | branch={st.get('branch_name')}"
        )
    print("")

    # --- daily station PV energy ---
    station_by_day: dict[date, float] = {}
    with open(f"{BASE}/stationtelemetry_daily_energy.csv") as f:
        rd = csv.DictReader(f)
        for row in rd:
            d = _parse_day(row["day_local"])
            station_by_day[d] = float(row.get("today_generation_energy") or 0)

    days = sorted(station_by_day)
    if not days:
        print("No station daily energy rows")
        return
    end = days[-1]
    start = end - timedelta(days=LAST_N_DAYS - 1)
    pv_30 = [v for d, v in station_by_day.items() if start <= d <= end]

    print(f"Station PV energy (kWh/day) last {LAST_N_DAYS}d: {start} -> {end}")
    summarize("PV_kWh_day", pv_30)
    print("")

    # --- solartelemetry daily counters ---
    per_day_dev = defaultdict(dict)  # day -> device_id -> metrics
    with open(f"{BASE}/solartelemetry_daily_energy.csv") as f:
        rd = csv.DictReader(f)
        for row in rd:
            d = _parse_day(row["day_local"])
            dev = str(row["device_id"])
            per_day_dev[d][dev] = {
                "pv": float(row.get("daily_active_production") or 0),
                "load": float(row.get("daily_consumption") or 0),
                "buy": float(row.get("daily_energy_buy") or 0),
                "sell": float(row.get("daily_energy_sell") or 0),
            }

    both = 0
    identical = {"pv": 0, "load": 0, "buy": 0, "sell": 0}
    for d, devmap in per_day_dev.items():
        if len(devmap) >= 2:
            both += 1
            vals = list(devmap.values())
            for k in identical:
                if abs(vals[0][k] - vals[1][k]) < 1e-6:
                    identical[k] += 1

    # decide aggregation rule
    def agg_day(devmap: dict, key: str) -> float:
        vals = [v[key] for v in devmap.values()]
        # if almost always identical across devices, treat as duplicated totals
        if both > 0 and identical[key] / both >= 0.8:
            return max(vals)
        return sum(vals)

    pv_30, load_30, buy_30, sell_30 = [], [], [], []
    export_days = 0
    for d in sorted(per_day_dev):
        if not (start <= d <= end):
            continue
        dm = per_day_dev[d]
        pv = agg_day(dm, "pv")
        load = agg_day(dm, "load")
        buy = agg_day(dm, "buy")
        sell = agg_day(dm, "sell")
        pv_30.append(pv)
        load_30.append(load)
        buy_30.append(buy)
        sell_30.append(sell)
        if sell > 0:
            export_days += 1

    print("Daily energy counters from main_solartelemetry (heuristic de-dup by device):")
    print(f" - days_with_2+devices={both} | identical_days(pv/load/buy/sell)={identical}")
    summarize("PV_kWh_day", pv_30)
    summarize("Load_kWh_day", load_30)
    summarize("GridBuy_kWh_day", buy_30)
    summarize("GridSell_kWh_day", sell_30)
    if sell_30:
        print(f" - days_with_any_export (sell>0): {export_days}/{len(sell_30)}")
    if load_30:
        avg_load = sum(load_30) / len(load_30)
        avg_buy = sum(buy_30) / len(buy_30) if buy_30 else 0.0
        print(f" - avg_grid_share_of_load ≈ {100.0*avg_buy/max(avg_load,1e-9):.1f}% (using daily energy counters)")
    print("")

    # --- SOC from station raw telemetry (unique station-level SOC) ---
    soc = []
    hi90 = hi95 = lo20 = lo10 = 0
    with open(f"{BASE}/stationtelemetry_raw_last_30d.csv") as f:
        rd = csv.DictReader(f)
        for row in rd:
            s = row.get("battery_soc")
            if s in (None, ""):
                continue
            v = float(s)
            soc.append(v)
            if v >= 90:
                hi90 += 1
            if v >= 95:
                hi95 += 1
            if v <= 20:
                lo20 += 1
            if v <= 10:
                lo10 += 1

    if soc:
        soc.sort()
        print("Battery SOC distribution (stationtelemetry last 30d):")
        print(
            f" - samples={len(soc)} min={soc[0]:.1f}% p50={_percentile(soc,0.5):.1f}% p90={_percentile(soc,0.9):.1f}% max={soc[-1]:.1f}%"
        )
        print(
            f" - time>=90%: {100*hi90/len(soc):.1f}% | >=95%: {100*hi95/len(soc):.1f}% | <=20%: {100*lo20/len(soc):.1f}% | <=10%: {100*lo10/len(soc):.1f}%"
        )
    else:
        print("No SOC samples found in stationtelemetry_raw_last_30d.csv")


if __name__ == "__main__":
    main()

