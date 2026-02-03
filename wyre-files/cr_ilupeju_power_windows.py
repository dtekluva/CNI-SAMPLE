#!/usr/bin/env python3
"""CR_Ilupeju: power (kW) percentiles for GEN + UTILITY in day windows."""

import os
import psycopg2

TZ = "Africa/Lagos"
MONTHS_BACK = 12
DEVICE_IDS = [194, 195]

WINDOWS = {
    "ALL_HOURS": None,
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

    for label, window in WINDOWS.items():
        if window is None:
            time_filter = ""
        else:
            t0, t1 = window
            time_filter = f"AND (post_datetime AT TIME ZONE '{TZ}')::time >= time '{t0}' AND (post_datetime AT TIME ZONE '{TZ}')::time <= time '{t1}'"

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
                {time_filter}
            )
            SELECT
              device_id,
              COUNT(*) AS n,
              percentile_cont(0.1) within group (order by total_kw) AS p10,
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

        rows = cur.fetchall()
        print(f"\nPOWER_STATS_WINDOW: {label}")
        for device_id, n, p10, p50, p90, p95, mx in rows:
            print(
                f"- device_id={device_id} | n={n:,} | p10={p10 or 0:,.1f} | p50={p50 or 0:,.1f} | "
                f"p90={p90 or 0:,.1f} | p95={p95 or 0:,.1f} | max={mx or 0:,.1f}"
            )

    conn.close()


if __name__ == "__main__":
    main()

