#!/usr/bin/env python3
"""Compare CR_Ilupeju energy in different daytime windows (GEN+UTILITY)."""

import os
import psycopg2

TZ = "Africa/Lagos"
MONTHS_BACK = 12
DEVICE_IDS = [194, 195]

WINDOWS = {
    "09:00-16:30": ("09:00:00", "16:30:00"),
    "07:00-18:00": ("07:00:00", "18:00:00"),
}


def read_credentials(path: str) -> dict:
    d = {}
    with open(path, "r") as f:
        for raw in f:
            line = raw.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def main() -> None:
    creds = read_credentials(os.path.join(os.path.dirname(__file__), ".credentials"))
    conn = psycopg2.connect(
        host=creds["host"],
        database="wyre_db",
        user=creds["user"],
        password=creds["password"],
        port=creds.get("port", "5432"),
    )
    cur = conn.cursor()

    # build SELECT pieces for each window
    window_exprs = []
    for label, (t0, t1) in WINDOWS.items():
        window_exprs.append(
            f"MIN(kwh_import) FILTER (WHERE local_ts::time >= time '{t0}' AND local_ts::time <= time '{t1}') AS min_{label.replace(':','').replace('-','_')},"
        )
        window_exprs.append(
            f"MAX(kwh_import) FILTER (WHERE local_ts::time >= time '{t0}' AND local_ts::time <= time '{t1}') AS max_{label.replace(':','').replace('-','_')},"
        )

    select_windows = "\n            ".join(window_exprs)

    cur.execute(
        f"""
        WITH latest AS (
          SELECT MAX(post_datetime) AS mx
          FROM main_reading
          WHERE device_id = ANY(%s)
        ), r AS (
          SELECT
            device_id,
            (post_datetime AT TIME ZONE %s) AS local_ts,
            kwh_import
          FROM main_reading, latest
          WHERE device_id = ANY(%s)
            AND kwh_import IS NOT NULL
            AND post_datetime >= (latest.mx - (%s || ' months')::interval)
        ), daily AS (
          SELECT
            device_id,
            date(local_ts) AS day,
            MIN(kwh_import) AS min_kwh,
            MAX(kwh_import) AS max_kwh,
            {select_windows.rstrip(',')}
          FROM r
          GROUP BY device_id, date(local_ts)
        ), daily_clean AS (
          SELECT
            device_id,
            day,
            GREATEST(0, max_kwh-min_kwh) AS kwh_total,
            {', '.join([
                f"GREATEST(0, COALESCE(max_{lbl.replace(':','').replace('-','_')},0)-COALESCE(min_{lbl.replace(':','').replace('-','_')},0)) AS kwh_{lbl.replace(':','').replace('-','_')}"
                for lbl in WINDOWS.keys()
            ])}
          FROM daily
        ), combined AS (
          SELECT
            day,
            SUM(kwh_total) AS kwh_total,
            {', '.join([f"SUM(kwh_{lbl.replace(':','').replace('-','_')}) AS kwh_{lbl.replace(':','').replace('-','_')}" for lbl in WINDOWS.keys()])}
          FROM daily_clean
          GROUP BY day
        )
        SELECT
          COUNT(*) AS days,
          AVG(kwh_total) AS avg_total,
          {', '.join([f"AVG(kwh_{lbl.replace(':','').replace('-','_')}) AS avg_{lbl.replace(':','').replace('-','_')}" for lbl in WINDOWS.keys()])}
        FROM combined;
        """,
        (DEVICE_IDS, TZ, DEVICE_IDS, MONTHS_BACK),
    )

    row = cur.fetchone()
    days = row[0]
    avg_total = row[1] or 0
    print(f"Days: {days}")
    print(f"Avg total: {avg_total:,.2f} kWh/day")

    idx = 2
    for label in WINDOWS.keys():
        avg = row[idx] or 0
        idx += 1
        print(f"Avg {label}: {avg:,.2f} kWh/day")

    conn.close()


if __name__ == "__main__":
    main()

