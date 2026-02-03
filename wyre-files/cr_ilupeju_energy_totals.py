#!/usr/bin/env python3
"""CR_Ilupeju (branch_id=83): totals for GEN + UTILITY over trailing window."""

import os
import psycopg2

TZ = "Africa/Lagos"
MONTHS_BACK = 12
DEVICE_IDS = [194, 195]


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
        ), daily_clean AS (
          SELECT
            device_id,
            day,
            CASE WHEN (max_kwh-min_kwh) > 0 THEN (max_kwh-min_kwh) ELSE 0 END AS kwh_day,
            CASE
              WHEN max_kwh_solar IS NOT NULL AND min_kwh_solar IS NOT NULL AND (max_kwh_solar-min_kwh_solar) > 0
              THEN (max_kwh_solar-min_kwh_solar)
              ELSE 0
            END AS kwh_solar
          FROM daily
        ), combined AS (
          SELECT day, SUM(kwh_day) AS kwh_day, SUM(kwh_solar) AS kwh_solar
          FROM daily_clean
          GROUP BY day
        )
        SELECT
          'PER_DEVICE' AS row_type,
          device_id::text,
          COUNT(*) AS days,
          SUM(kwh_day) AS total_kwh,
          SUM(kwh_solar) AS total_kwh_solar
        FROM daily_clean
        GROUP BY device_id
        UNION ALL
        SELECT
          'COMBINED' AS row_type,
          'BRANCH_TOTAL' AS device,
          COUNT(*) AS days,
          SUM(kwh_day) AS total_kwh,
          SUM(kwh_solar) AS total_kwh_solar
        FROM combined;
        """,
        (DEVICE_IDS, TZ, DEVICE_IDS, MONTHS_BACK),
    )

    print("TOTALS (trailing 12 months window anchored to latest):")
    for row_type, device, days, total_kwh, total_solar in cur.fetchall():
        print(
            f"- {row_type:<8} {device:<12} | days={days} | total_kwh={total_kwh or 0:,.1f} | solar_kwh={total_solar or 0:,.1f}"
        )

    conn.close()


if __name__ == "__main__":
    main()

