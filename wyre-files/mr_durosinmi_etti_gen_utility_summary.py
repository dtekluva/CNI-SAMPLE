#!/usr/bin/env python3
"""Mr Durosinmi Etti (client_id=4): summarize GEN + UTILITY devices.

Prints:
- candidate devices (GEN/UTILITY/grid-like)
- per-device period + samples
- 12-month trailing energy totals and peak power stats (combined)

Note: GEN/UTILITY meters are treated as alternate supply sources; combining daily deltas
provides approximate site energy when meters are healthy.
"""

import os
import psycopg2
from typing import Optional

CLIENT_ID = 4
TZ = "Africa/Lagos"
MONTHS_BACK = 12


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


def looks_like_grid(name: str) -> bool:
    n = (name or "").lower()
    keys = ["utility", "grid", "ekedc", "ikedc", "aedc", "ibedc", "jedc", "kedco", "bedc", "phcn"]
    return any(k in n for k in keys)


def looks_like_gen(name: str) -> bool:
    n = (name or "").lower()
    keys = ["gen", "genset", "generator", "dg", "diesel"]
    return any(n.startswith(k) for k in ["gen"]) or any(k in n for k in keys)


def classify_role(name: str, fuel_type: Optional[str]) -> str:
    """Best-effort label for supply meters."""
    if looks_like_grid(name):
        return "UTILITY"
    if (fuel_type or "").upper() in {"DIESEL", "PETROL", "GAS"}:
        return "GEN"
    if looks_like_gen(name):
        return "GEN"
    return "OTHER"


def window_filter_sql(start: Optional[str], end: Optional[str]) -> str:
    if not start or not end:
        return ""
    return f"AND local_ts::time >= time '{start}' AND local_ts::time <= time '{end}'"


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

    cur.execute("SELECT id,name,client_type,is_active FROM account_client WHERE id=%s", (CLIENT_ID,))
    print("CLIENT:", cur.fetchone())

    cur.execute(
        """
        SELECT d.id, d.name, d.device_id, d.fuel_type, d.is_active, COALESCE(b.id,0) AS branch_id, COALESCE(b.name,'')
        FROM main_device d
        LEFT JOIN main_branch b ON b.id=d.branch_id
        WHERE COALESCE(b.client_id, d.client_id) = %s
        ORDER BY d.is_active DESC, d.id;
        """,
        (CLIENT_ID,),
    )
    devices = cur.fetchall()

    candidates = []
    for dev_id, name, serial, fuel, active, branch_id, branch_name in devices:
        if not active:
            continue
        role = classify_role(name, fuel)
        if role in {"UTILITY", "GEN"}:
            candidates.append((dev_id, name, serial, fuel, branch_id, branch_name, role))

    if not candidates:
        print("No active GEN/GRID/UTILITY-like devices found.")
        conn.close()
        return

    dev_ids = [c[0] for c in candidates]

    # Anchor window to the most recent reading across candidates
    cur.execute(
        "SELECT MAX(post_datetime) FROM main_reading WHERE device_id = ANY(%s)",
        (dev_ids,),
    )
    anchor = cur.fetchone()[0]
    if not anchor:
        print("No readings found for candidate devices.")
        conn.close()
        return

    # per-device period + samples (left join to include devices with 0 readings)
    cur.execute(
        f"""
        SELECT d.id, d.name,
               MIN(r.post_datetime AT TIME ZONE %s) AS mn,
               MAX(r.post_datetime AT TIME ZONE %s) AS mx,
               COUNT(*) AS cnt
        FROM main_device d
        LEFT JOIN main_reading r ON r.device_id=d.id
        WHERE d.id = ANY(%s)
        GROUP BY d.id, d.name
        ORDER BY d.id;
        """,
        (TZ, TZ, dev_ids),
    )
    print("\nGEN/UTILITY CANDIDATES (period in Africa/Lagos):")
    # map: device_id -> (name, mn, mx, cnt)
    period = {row[0]: row[1:] for row in cur.fetchall()}
    for dev_id, name, serial, fuel, branch_id, branch_name, role in candidates:
        _nm, mn, mx, cnt = period.get(dev_id, (name, None, None, 0))
        print(
            f"- {dev_id} ({name}) | role={role} | fuel={fuel or 'N/A'} | branch={branch_name} | "
            f"{mn} -> {mx} | samples={cnt:,}"
        )

    def energy_block(label: str, start: Optional[str], end: Optional[str]) -> None:
        tf = window_filter_sql(start, end)
        cur.execute(
            f"""
            WITH r AS (
              SELECT
                device_id,
                (post_datetime AT TIME ZONE %s) AS local_ts,
                kwh_import
              FROM main_reading
              WHERE device_id = ANY(%s)
                AND kwh_import IS NOT NULL
                AND post_datetime >= (%s - (%s || ' months')::interval)
            ), daily AS (
              SELECT
                device_id,
                date(local_ts) AS day,
                MIN(kwh_import) AS min_kwh,
                MAX(kwh_import) AS max_kwh
              FROM r
              WHERE 1=1 {tf}
              GROUP BY device_id, date(local_ts)
            ), daily_clean AS (
              SELECT device_id, day, GREATEST(0, (max_kwh-min_kwh)) AS kwh_day
              FROM daily
              WHERE (max_kwh-min_kwh) > 0
            ), combined AS (
              SELECT day, SUM(kwh_day) AS kwh_day
              FROM daily_clean
              GROUP BY day
            )
            SELECT
              (SELECT COUNT(*) FROM combined) AS days,
              (SELECT SUM(kwh_day) FROM combined) AS total_kwh,
              (SELECT AVG(kwh_day) FROM combined) AS avg_kwh_day,
              (SELECT MAX(kwh_day) FROM combined) AS max_kwh_day;
            """,
            (TZ, dev_ids, anchor, MONTHS_BACK),
        )
        days, total_kwh, avg_kwh_day, max_kwh_day = cur.fetchone()
        print(f"\n{label} ENERGY (combined meters):")
        print(f"- Days with data: {days}")
        print(f"- Total energy: {total_kwh or 0:,.1f} kWh")
        print(f"- Avg energy/day: {avg_kwh_day or 0:,.2f} kWh/day")
        print(f"- Max energy/day: {max_kwh_day or 0:,.2f} kWh/day")

    energy_block("TRAILING-12MO FULL-DAY", None, None)
	    energy_block("TRAILING-12MO 07:00-18:00", "07:00:00", "18:00:00")
	    energy_block("TRAILING-12MO 09:00-16:30", "09:00:00", "16:30:00")

    # Power stats (full 12-month window)
    cur.execute(
        """
        WITH r AS (
          SELECT device_id, total_kw
          FROM main_reading
          WHERE device_id = ANY(%s)
            AND total_kw IS NOT NULL
            AND post_datetime >= (%s - (%s || ' months')::interval)
        )
        SELECT
          device_id,
          percentile_cont(0.5) within group (order by total_kw) AS p50_kw,
          percentile_cont(0.9) within group (order by total_kw) AS p90_kw,
          percentile_cont(0.95) within group (order by total_kw) AS p95_kw,
          MAX(total_kw) AS max_kw
        FROM r
        GROUP BY device_id
        ORDER BY device_id;
        """,
        (dev_ids, anchor, MONTHS_BACK),
    )
    power_rows = cur.fetchall()
    peak_kw = max((r[4] or 0) for r in power_rows) if power_rows else 0
    print("\nPOWER (per meter; trailing window):")
    for device_id, p50, p90, p95, mx in power_rows:
        nm = next((c[1] for c in candidates if c[0] == device_id), str(device_id))
        print(f"- {device_id} ({nm}): p50={p50 or 0:,.1f} kW | p90={p90 or 0:,.1f} | p95={p95 or 0:,.1f} | max={mx or 0:,.1f}")
    print(f"\nPeak observed kW (max across meters): {peak_kw:,.1f} kW")

    conn.close()


if __name__ == "__main__":
    main()

