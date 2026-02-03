#!/usr/bin/env python3
"""Meadow Hall: estimate PV + battery sizing for target % energy offset.

Uses EKEDC meter (device 220) as the baseline unless you extend it.
Sizing uses PV yield = kWp * PSH * PR (not 24h generation).
"""

import os
import psycopg2

CLIENT_NAME = "Meadow Hall"
UTILITY_DEVICE_ID = 220  # EKEDC

MONTHS_BACK = 12

# PV yield assumptions (Nigeria/Lagos typical; adjust with site survey)
PSH = 5.0  # peak sun hours/day
PR = 0.75  # performance ratio (losses)

# Storage assumptions
BATTERY_ROUND_TRIP_EFF = 0.90
BATTERY_DOD = 0.80
BATTERY_EOL_RETAIN = 0.80

TARGET_OFFSET = 0.70  # 70% energy savings / offset
TARIFF_NGN_PER_KWH = 226


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


def daily_kwh(cur, device_id: int, solar_window: bool):
    time_filter = "" if not solar_window else "AND local_ts::time >= time '09:00:00' AND local_ts::time <= time '16:30:00'"
    cur.execute(
        f"""
        WITH r AS (
          SELECT (post_datetime AT TIME ZONE 'Africa/Lagos') AS local_ts, kwh_import
          FROM main_reading
          WHERE device_id=%s AND kwh_import IS NOT NULL
            AND post_datetime >= (date_trunc('day', now()) - (%s || ' months')::interval)
        ), d AS (
          SELECT date(local_ts) AS day,
                 min(kwh_import) AS min_kwh,
                 max(kwh_import) AS max_kwh
          FROM r
          WHERE 1=1 {time_filter}
          GROUP BY 1
        )
        SELECT count(*) AS days,
               avg(max_kwh-min_kwh) AS avg_kwh_day,
               percentile_cont(0.5) within group (order by (max_kwh-min_kwh)) AS median_kwh_day
        FROM d
        WHERE max_kwh IS NOT NULL AND min_kwh IS NOT NULL AND (max_kwh-min_kwh) > 0;
        """,
        (device_id, MONTHS_BACK),
    )
    return cur.fetchone()  # (days, avg, median)


def power_stats(cur, device_id: int):
    cur.execute(
        """
        WITH r AS (
          SELECT total_kw
          FROM main_reading
          WHERE device_id=%s AND total_kw IS NOT NULL
            AND post_datetime >= (date_trunc('day', now()) - (%s || ' months')::interval)
        )
        SELECT avg(total_kw),
               percentile_cont(0.5) within group (order by total_kw),
               percentile_cont(0.9) within group (order by total_kw),
               percentile_cont(0.95) within group (order by total_kw),
               max(total_kw)
        FROM r;
        """,
        (device_id, MONTHS_BACK),
    )
    return cur.fetchone()


def round_up(x: float, step: float) -> float:
    if x <= 0:
        return 0
    return step * int((x + step - 1e-9) // step + 1)


def main():
    creds = read_credentials(os.path.join(os.path.dirname(__file__), ".credentials"))
    conn = psycopg2.connect(
        host=creds["host"],
        database="wyre_db",
        user=creds["user"],
        password=creds["password"],
        port=creds.get("port", "5432"),
    )
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM account_client WHERE name ILIKE %s LIMIT 5", (f"%{CLIENT_NAME}%",))
    print("CLIENT_MATCHES:", cur.fetchall())

    total_days, total_avg, total_med = daily_kwh(cur, UTILITY_DEVICE_ID, solar_window=False)
    day_days, day_avg, day_med = daily_kwh(cur, UTILITY_DEVICE_ID, solar_window=True)

    night_avg = (total_avg or 0) - (day_avg or 0)

    print(f"\nUtility meter device_id={UTILITY_DEVICE_ID}")
    print(f"Daily total avg: {total_avg:,.2f} kWh/day (days={total_days})")
    print(f"Day (09:00-16:30) avg: {day_avg:,.2f} kWh/day")
    print(f"Night/other-hours avg: {night_avg:,.2f} kWh/day")

    avg_kw, p50, p90, p95, mx = power_stats(cur, UTILITY_DEVICE_ID)
    print(f"\nPower (kW) stats: avg={avg_kw:,.1f}, p50={p50:,.1f}, p90={p90:,.1f}, p95={p95:,.1f}, max={mx:,.1f}")

    # Target energy offset
    target_kwh = (total_avg or 0) * TARGET_OFFSET

    # PV direct usage limited by actual daytime consumption
    direct_kwh = min(day_avg or 0, target_kwh)
    battery_delivered_kwh = max(0.0, target_kwh - direct_kwh)

    # PV must cover direct energy + charge energy (account for round-trip losses)
    pv_kwh_needed = direct_kwh + (battery_delivered_kwh / BATTERY_ROUND_TRIP_EFF if BATTERY_ROUND_TRIP_EFF else 0)
    pv_kwp = pv_kwh_needed / (PSH * PR) if (PSH * PR) else 0
    pv_kwp_rec = round_up(pv_kwp, 10)  # commercial: 10kWp blocks

    # Battery nominal energy capacity (kWh)
    battery_nominal = battery_delivered_kwh / (BATTERY_DOD * BATTERY_EOL_RETAIN) if (BATTERY_DOD * BATTERY_EOL_RETAIN) else 0
    battery_nominal_rec = round_up(battery_nominal, 50)  # size in 50kWh blocks

    annual_offset_kwh = target_kwh * 365
    annual_savings = annual_offset_kwh * TARIFF_NGN_PER_KWH

    print("\n--- RECOMMENDED HYBRID SOLAR + STORAGE (ENERGY BASIS) ---")
    print(f"Target offset: {TARGET_OFFSET*100:.0f}% of total energy = {target_kwh:,.2f} kWh/day")
    print(f"PV energy needed/day (incl. storage losses): {pv_kwh_needed:,.2f} kWh/day")
    print(f"PV size estimate: {pv_kwp:,.1f} kWp  (recommended: {pv_kwp_rec:,.0f} kWp)")
    print(f"Battery delivered/night: {battery_delivered_kwh:,.2f} kWh/day")
    print(f"Battery nominal capacity: {battery_nominal:,.1f} kWh  (recommended: {battery_nominal_rec:,.0f} kWh)")
    print(f"Annual energy offset: {annual_offset_kwh:,.0f} kWh/year")
    print(f"Annual savings @ \u20a6{TARIFF_NGN_PER_KWH}/kWh: \u20a6{annual_savings:,.0f}/year")

    conn.close()


if __name__ == "__main__":
    main()

