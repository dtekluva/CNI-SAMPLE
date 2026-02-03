#!/usr/bin/env python3
"""Export month-to-month peak kW per device for Meadow Hall.

Outputs peaks for:
- overall monthly peak
- day peak (06:00-18:00)
- night peak (18:00-06:00)
- solar-window peak (09:00-16:30)

Writes CSV: wyre-files/meadow_hall_monthly_peaks_by_device.csv
"""

import csv
import os
from typing import Optional

import psycopg2

CLIENT_NAME = "Meadow Hall"
MONTHS_BACK = 12
TZ = "Africa/Lagos"

DAY_START = "06:00:00"
DAY_END = "18:00:00"
SOLAR_START = "09:00:00"
SOLAR_END = "16:30:00"

OUT_CSV = os.path.join(os.path.dirname(__file__), "meadow_hall_monthly_peaks_by_device.csv")


def read_credentials(path: str) -> dict:
    creds = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            creds[k.strip()] = v.strip()
    return creds


def pick_device_table(cur) -> Optional[str]:
    """Pick a device table that can map device_id -> (client_id, name)."""
    preferred = ["main_device", "account_device", "device_device", "devices_device", "meter_device"]

    def cols(table: str) -> set[str]:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema='public' AND table_name=%s
            """,
            (table,),
        )
        return {r[0] for r in cur.fetchall()}

    def exists(table: str) -> bool:
        cur.execute("SELECT to_regclass(%s)", (f"public.{table}",))
        return cur.fetchone()[0] is not None

    def is_good(table: str) -> bool:
        c = cols(table)
        return "id" in c and "client_id" in c and ("name" in c or "device_name" in c or "label" in c)

    for t in preferred:
        if exists(t) and is_good(t):
            return t

    # fallback: any table with (id, client_id, name-ish)
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.columns
        WHERE table_schema='public'
        GROUP BY table_name
        HAVING bool_or(column_name='id')
           AND bool_or(column_name='client_id')
           AND (bool_or(column_name='name') OR bool_or(column_name='device_name') OR bool_or(column_name='label'))
        ORDER BY table_name
        """
    )
    rows = cur.fetchall()
    return rows[0][0] if rows else None


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
        "SELECT id, name FROM account_client WHERE name ILIKE %s ORDER BY is_active DESC, id LIMIT 5",
        (f"%{CLIENT_NAME}%",),
    )
    matches = cur.fetchall()
    if not matches:
        raise SystemExit(f"No client found matching {CLIENT_NAME!r}")
    client_id, client_name = matches[0]

    device_table = pick_device_table(cur)
    if not device_table:
        raise SystemExit("Could not find a device table with client_id + name")

    # name expression
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s
        """,
        (device_table,),
    )
    c = {r[0] for r in cur.fetchall()}
    if "name" in c:
        name_expr = "d.name"
    elif "device_name" in c:
        name_expr = "d.device_name"
    else:
        name_expr = "d.label"

    sql = f"""
    WITH r AS (
      SELECT device_id,
             (post_datetime AT TIME ZONE '{TZ}') AS local_ts,
             total_kw
      FROM main_reading
      WHERE total_kw IS NOT NULL
        AND post_datetime >= (date_trunc('month', now()) - (%s || ' months')::interval)
    )
    SELECT
      r.device_id,
      {name_expr} AS device_name,
      date_trunc('month', r.local_ts)::date AS month,
      count(*) AS samples,
      max(r.total_kw) AS peak_kw,
      max(r.total_kw) FILTER (WHERE r.local_ts::time >= time '{DAY_START}' AND r.local_ts::time < time '{DAY_END}') AS day_peak_kw,
      max(r.total_kw) FILTER (WHERE NOT (r.local_ts::time >= time '{DAY_START}' AND r.local_ts::time < time '{DAY_END}')) AS night_peak_kw,
      max(r.total_kw) FILTER (WHERE r.local_ts::time >= time '{SOLAR_START}' AND r.local_ts::time <= time '{SOLAR_END}') AS solar_window_peak_kw
    FROM r
    JOIN {device_table} d ON d.id = r.device_id
    WHERE d.client_id = %s
    GROUP BY r.device_id, device_name, month
    ORDER BY r.device_id, month;
    """

    cur.execute(sql, (MONTHS_BACK, client_id))
    rows = cur.fetchall()

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "client_id",
                "client_name",
                "device_table",
                "device_id",
                "device_name",
                "month",
                "samples",
                "peak_kw",
                "day_peak_kw",
                "night_peak_kw",
                "solar_window_peak_kw",
            ]
        )
        for device_id, device_name, month, samples, peak, day_peak, night_peak, solar_peak in rows:
            w.writerow([client_id, client_name, device_table, device_id, device_name, month, samples, peak, day_peak, night_peak, solar_peak])

    print(f"Client: {client_name} (id={client_id})")
    print(f"Device table used: {device_table}")
    print(f"Rows exported: {len(rows)}")
    print(f"CSV: {OUT_CSV}")

    # Print a short preview
    for r in rows[:15]:
        print(r)

    conn.close()


if __name__ == "__main__":
    main()

