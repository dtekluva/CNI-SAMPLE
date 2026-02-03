#!/usr/bin/env python3
"""Chicken Republic - CR_Ilupeju (branch_id=83): solar sizing inputs.

Focus: GEN + UTILITY devices.
Computes 12-month trailing energy (daily avg) and power stats.
"""

import os
import psycopg2

BRANCH_ID = 83
CLIENT_ID = 27
DEVICE_IDS = [194, 195]  # GEN_170kVA, UTILITY
TZ = "Africa/Lagos"
MONTHS_BACK = 12

PSH = 5.0
PR = 0.75


def read_credentials(path: str) -> dict:
    creds = {}
    with open(path, "r") as f:
        for raw in f:
            line = raw.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            creds[k.strip()] = v.strip()
    return creds


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

    cur.execute("SELECT id,name,address FROM main_branch WHERE id=%s", (BRANCH_ID,))
    print("BRANCH:", cur.fetchone())

    cur.execute(
        "SELECT id,name,device_id FROM main_device WHERE id = ANY(%s) ORDER BY id",
        (DEVICE_IDS,),
    )
    print("DEVICES:")
    for r in cur.fetchall():
        print("-", r)

    # Trailing window anchored to latest timestamp among selected devices
    cur.execute(
        "SELECT MAX(post_datetime) FROM main_reading WHERE device_id = ANY(%s)",
        (DEVICE_IDS,),
    )
    latest = cur.fetchone()[0]
    print("LATEST_TS_UTC:", latest)

    # Energy (kWh/day) stats per device and combined
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
            MIN(kwh_import) FILTER (
              WHERE local_ts::time >= time '09:00:00' AND local_ts::time <= time '16:30:00'
            ) AS min_kwh_solar,
            MAX(kwh_import) FILTER (
              WHERE local_ts::time >= time '09:00:00' AND local_ts::time <= time '16:30:00'
            ) AS max_kwh_solar
          FROM r
          GROUP BY device_id, date(local_ts)
        ), per_device AS (
          SELECT
            device_id,
            COUNT(*) FILTER (WHERE (max_kwh-min_kwh) > 0) AS days,
            AVG(max_kwh-min_kwh) FILTER (WHERE (max_kwh-min_kwh) > 0) AS avg_kwh_day,
            AVG(max_kwh_solar-min_kwh_solar) FILTER (WHERE max_kwh_solar IS NOT NULL AND min_kwh_solar IS NOT NULL AND (max_kwh_solar-min_kwh_solar) > 0) AS avg_kwh_solar
          FROM daily
          GROUP BY device_id
        ), combined_daily AS (
          SELECT
            day,
            SUM(CASE WHEN (max_kwh-min_kwh) > 0 THEN (max_kwh-min_kwh) ELSE 0 END) AS kwh_day,
            SUM(CASE WHEN max_kwh_solar IS NOT NULL AND min_kwh_solar IS NOT NULL AND (max_kwh_solar-min_kwh_solar) > 0 THEN (max_kwh_solar-min_kwh_solar) ELSE 0 END) AS kwh_solar
          FROM daily
          GROUP BY day
        )
        SELECT
          'PER_DEVICE' AS row_type,
          device_id::text,
          days,
          avg_kwh_day,
          avg_kwh_solar
        FROM per_device
        UNION ALL
        SELECT
          'COMBINED' AS row_type,
          'BRANCH_TOTAL' AS device,
          COUNT(*) AS days,
          AVG(kwh_day) AS avg_kwh_day,
          AVG(kwh_solar) AS avg_kwh_solar
        FROM combined_daily;
        """,
        (DEVICE_IDS, TZ, DEVICE_IDS, MONTHS_BACK),
    )

    print("\nENERGY_STATS (kWh/day):")
    rows = cur.fetchall()
    for row_type, device, days, avg_day, avg_solar in rows:
        night = (avg_day or 0) - (avg_solar or 0)
        print(
            f"- {row_type:<8} {device:<12} | days={days} | total_avg={avg_day or 0:,.2f} | "
            f"solar_avg={avg_solar or 0:,.2f} | night/other={night:,.2f}"
        )

    # Power stats (kW)
    cur.execute(
        f"""
        WITH latest AS (
          SELECT MAX(post_datetime) AS mx
          FROM main_reading
          WHERE device_id = ANY(%s)
        ), r AS (
          SELECT device_id, total_kw
          FROM main_reading, latest
          WHERE device_id = ANY(%s)
            AND total_kw IS NOT NULL
            AND post_datetime >= (latest.mx - (%s || ' months')::interval)
        )
        SELECT
          device_id,
          AVG(total_kw) AS avg_kw,
          percentile_cont(0.5) within group (order by total_kw) AS p50,
          percentile_cont(0.9) within group (order by total_kw) AS p90,
          percentile_cont(0.95) within group (order by total_kw) AS p95,
          MAX(total_kw) AS mx
        FROM r
        GROUP BY device_id
        ORDER BY device_id;
        """,
        (DEVICE_IDS, DEVICE_IDS, MONTHS_BACK),
    )

    print("\nPOWER_STATS (kW):")
    for device_id, avg_kw, p50, p90, p95, mx in cur.fetchall():
        print(
            f"- device_id={device_id} | avg={avg_kw or 0:,.1f} | p50={p50 or 0:,.1f} | "
            f"p90={p90 or 0:,.1f} | p95={p95 or 0:,.1f} | max={mx or 0:,.1f}"
        )

    print(f"\nPV_YIELD_ASSUMPTION: PSH={PSH}, PR={PR} => {PSH*PR:.2f} kWh/day per kWp")

    conn.close()


if __name__ == "__main__":
    main()

