#!/usr/bin/env python3
"""Export solar telemetry for Mr Durosinmi Etti (client_id=4) to CSV.

Exports:
- Branch list for client
- Installed station + solar device metadata
- Daily energy summaries (PV, load, grid buy/sell)
- Raw last-N-days telemetry (station + solar)

Read-only: does not modify the DB.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime

import psycopg2

CLIENT_ID = 4
TZ = "Africa/Lagos"
RAW_DAYS = 30
OUT_DIR = os.path.join("wyre-files", "output", "etti_solar_telemetry")


def read_credentials() -> dict:
    creds = {}
    with open(os.path.join("wyre-files", ".credentials")) as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            creds[k.strip()] = v.strip()
    return creds


def export_query(cur, path: str, query: str, params: tuple = ()) -> int:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cur.execute(query, params)
    cols = [d[0] for d in cur.description]
    n = 0
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        while True:
            rows = cur.fetchmany(5000)
            if not rows:
                break
            w.writerows(rows)
            n += len(rows)
    return n


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    creds = read_credentials()
    conn = psycopg2.connect(
        host=creds["host"],
        database="wyre_db",
        user=creds["user"],
        password=creds["password"],
        port=creds.get("port", "5432"),
    )
    cur = conn.cursor()

    # Branches
    branches_csv = os.path.join(OUT_DIR, "branches.csv")
    n_br = export_query(
        cur,
        branches_csv,
        """
        SELECT id AS branch_id, name AS branch_name, address, city, region_id,
               utility_tariff, email, copy_email, is_active
        FROM main_branch
        WHERE client_id=%s
        ORDER BY id
        """,
        (CLIENT_ID,),
    )

    # Station + solardevices metadata
    station_csv = os.path.join(OUT_DIR, "station.csv")
    n_station = export_query(
        cur,
        station_csv,
        """
        SELECT s.id AS station_pk, s.deye_station_id, s.name, s.address,
               s.installed_capacity, s.installed_battery_capacity,
               s.branch_id, b.name AS branch_name
        FROM main_station s
        JOIN main_branch b ON b.id=s.branch_id
        WHERE b.client_id=%s
        ORDER BY s.branch_id, s.id
        """,
        (CLIENT_ID,),
    )

    solardev_csv = os.path.join(OUT_DIR, "solardevices.csv")
    n_sd = export_query(
        cur,
        solardev_csv,
        """
        SELECT sd.id AS solardev_pk, sd.serial, sd.device_type, sd.model, sd.capacity_kwp,
               sd.status, sd.is_active, sd.branch_id, b.name AS branch_name, sd.created_at
        FROM main_solardevices sd
        JOIN main_branch b ON b.id=sd.branch_id
        WHERE b.client_id=%s
        ORDER BY sd.branch_id, sd.id
        """,
        (CLIENT_ID,),
    )

    # Period and device breakdown (solartelemetry)
    stats_csv = os.path.join(OUT_DIR, "solartelemetry_device_stats.csv")
    n_stats = export_query(
        cur,
        stats_csv,
        f"""
        SELECT t.branch_id,
               t.device_id,
               MIN(t.timestamp) AS ts_min_utc,
               MAX(t.timestamp) AS ts_max_utc,
               COUNT(*) AS rows,
               MAX(t.pv_power) AS pv_power_max,
               MAX(t.load_power) AS load_power_max,
               MAX(ABS(t.battery_power)) AS battery_power_abs_max,
               MAX(ABS(t.grid_power)) AS grid_power_abs_max
        FROM main_solartelemetry t
        JOIN main_branch b ON b.id=t.branch_id
        WHERE b.client_id=%s
        GROUP BY t.branch_id, t.device_id
        ORDER BY t.branch_id, t.device_id
        """,
        (CLIENT_ID,),
    )

    # Daily energy summary from solartelemetry (max of daily counters per local day)
    daily_solar_csv = os.path.join(OUT_DIR, "solartelemetry_daily_energy.csv")
    n_daily_solar = export_query(
        cur,
        daily_solar_csv,
        f"""
        SELECT date(t.timestamp AT TIME ZONE '{TZ}') AS day_local,
               t.branch_id,
               t.device_id,
               MAX(t.daily_active_production) AS daily_active_production,
               MAX(t.daily_consumption) AS daily_consumption,
               MAX(t.daily_energy_buy) AS daily_energy_buy,
               MAX(t.daily_energy_sell) AS daily_energy_sell
        FROM main_solartelemetry t
        JOIN main_branch b ON b.id=t.branch_id
        WHERE b.client_id=%s
        GROUP BY 1,2,3
        ORDER BY 1,2,3
        """,
        (CLIENT_ID,),
    )

    # Daily energy summary from stationtelemetry
    daily_station_csv = os.path.join(OUT_DIR, "stationtelemetry_daily_energy.csv")
    n_daily_station = export_query(
        cur,
        daily_station_csv,
        f"""
        SELECT date(t.timestamp AT TIME ZONE '{TZ}') AS day_local,
               t.branch_id,
               MAX(t.today_generation_energy) AS today_generation_energy
        FROM main_stationtelemetry t
        JOIN main_branch b ON b.id=t.branch_id
        WHERE b.client_id=%s
        GROUP BY 1,2
        ORDER BY 1,2
        """,
        (CLIENT_ID,),
    )

    # Raw last-N-days exports
    raw_solar_csv = os.path.join(OUT_DIR, f"solartelemetry_raw_last_{RAW_DAYS}d.csv")
    n_raw_solar = export_query(
        cur,
        raw_solar_csv,
        f"""
        SELECT t.*
        FROM main_solartelemetry t
        JOIN main_branch b ON b.id=t.branch_id
        WHERE b.client_id=%s
          AND t.timestamp >= (now() - interval '{RAW_DAYS} days')
        ORDER BY t.timestamp
        """,
        (CLIENT_ID,),
    )

    raw_station_csv = os.path.join(OUT_DIR, f"stationtelemetry_raw_last_{RAW_DAYS}d.csv")
    n_raw_station = export_query(
        cur,
        raw_station_csv,
        f"""
        SELECT t.*
        FROM main_stationtelemetry t
        JOIN main_branch b ON b.id=t.branch_id
        WHERE b.client_id=%s
          AND t.timestamp >= (now() - interval '{RAW_DAYS} days')
        ORDER BY t.timestamp
        """,
        (CLIENT_ID,),
    )

    conn.close()

    print("Export complete:")
    print(" -", branches_csv, f"({n_br} rows)")
    print(" -", station_csv, f"({n_station} rows)")
    print(" -", solardev_csv, f"({n_sd} rows)")
    print(" -", stats_csv, f"({n_stats} rows)")
    print(" -", daily_solar_csv, f"({n_daily_solar} rows)")
    print(" -", daily_station_csv, f"({n_daily_station} rows)")
    print(" -", raw_solar_csv, f"({n_raw_solar} rows)")
    print(" -", raw_station_csv, f"({n_raw_station} rows)")


if __name__ == "__main__":
    main()

