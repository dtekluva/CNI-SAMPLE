#!/usr/bin/env python3
"""Compute solar-hours energy use + PV size recommendation for a client."""

import os
import psycopg2

CLIENT_NAME = "Mr Durosinmi Etti"
TARIFF_NGN_PER_KWH = 226
PSH = 5.0  # peak sun hours (avg)
PR = 0.75  # performance ratio (losses)
MONTHS_BACK = 6  # keep fast; adjust to 12 when needed


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


def daily_stats(cur, device_id: int, solar_window: bool):
    time_filter = "" if not solar_window else "AND local_ts::time >= time '09:00:00' AND local_ts::time <= time '16:30:00'"
    cur.execute(
        f"""
        WITH r AS (
          SELECT (post_datetime AT TIME ZONE 'Africa/Lagos') AS local_ts, kwh_import
          FROM main_reading
          WHERE device_id=%s AND kwh_import IS NOT NULL
            AND post_datetime >= (date_trunc('day', now()) - (%s || ' months')::interval)
        ), d AS (
          SELECT date(local_ts) AS day, min(kwh_import) AS min_kwh, max(kwh_import) AS max_kwh
          FROM r
          WHERE 1=1 {time_filter}
          GROUP BY 1
        )
        SELECT count(*) AS days,
               avg(max_kwh-min_kwh) AS avg_daily_kwh,
               percentile_cont(0.5) within group (order by (max_kwh-min_kwh)) AS median_daily_kwh
        FROM d
        WHERE max_kwh IS NOT NULL AND min_kwh IS NOT NULL AND (max_kwh-min_kwh) > 0;
        """,
        (device_id, MONTHS_BACK),
    )
    return cur.fetchone()


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

    cur.execute(
        """SELECT id, name, client_type, is_active
           FROM account_client
           WHERE name ILIKE %s
           ORDER BY is_active DESC, id ASC""",
        (f"%{CLIENT_NAME}%",),
    )
    rows = cur.fetchall()
    if not rows:
        raise SystemExit(f"Client not found: {CLIENT_NAME}")
    client_id, name, client_type, is_active = rows[0]

    print(f"Client: {name} (id={client_id}, type={client_type}, active={is_active})")

    cur.execute(
        """SELECT d.id, d.name, d.fuel_type, d.is_active, COALESCE(b.name,'')
           FROM main_device d
           LEFT JOIN main_branch b ON b.id=d.branch_id
           WHERE COALESCE(b.client_id, d.client_id) = %s
           ORDER BY d.is_active DESC, d.id""",
        (client_id,),
    )
    devices = cur.fetchall()

    active_devices = [(dev_id, dev_name, fuel_type, branch_name)
                      for (dev_id, dev_name, fuel_type, dev_active, branch_name) in devices
                      if dev_active]
    dev_ids = [d[0] for d in active_devices]
    if not dev_ids:
        raise SystemExit("No active devices found for this client.")

    # Get reading counts for the recent window in one query (much faster than per-device COUNT(*))
    cur.execute(
        """
        SELECT device_id, count(*)
        FROM main_reading
        WHERE device_id = ANY(%s)
          AND post_datetime >= (date_trunc('day', now()) - (%s || ' months')::interval)
        GROUP BY device_id
        """,
        (dev_ids, MONTHS_BACK),
    )
    counts = dict(cur.fetchall())

    # Prefer obvious grid/utility meters, but also keep top devices by activity
    def looks_like_grid(name: str) -> bool:
        n = (name or "").lower()
        keys = ["utility", "grid", "ekedc", "ikedc", "aedc", "ibedc", "jedc", "kedco", "bedc", "phcn"]
        return any(k in n for k in keys)

    grid_like = [d for d in active_devices if counts.get(d[0], 0) > 0 and looks_like_grid(d[1])]
    by_count = sorted([d for d in active_devices if counts.get(d[0], 0) > 0], key=lambda d: counts.get(d[0], 0), reverse=True)

    selected = []
    seen = set()
    for d in grid_like + by_count[:10]:
        if d[0] in seen:
            continue
        seen.add(d[0])
        selected.append(d)

    # Compute stats only for selected devices
    candidates = []
    for dev_id, dev_name, fuel_type, branch_name in selected:
        reading_count = counts.get(dev_id, 0)
        solar = daily_stats(cur, dev_id, solar_window=True)
        full = daily_stats(cur, dev_id, solar_window=False)
        candidates.append((dev_id, dev_name, fuel_type, branch_name, reading_count, solar, full))

    if not candidates:
        raise SystemExit("No active devices with readings found for this client.")

    # Rank by solar-hours average daily kWh
    candidates.sort(key=lambda r: (r[5][1] or 0), reverse=True)

    print(f"\nTop devices by solar-hours energy (last {MONTHS_BACK} months):")
    for dev_id, dev_name, fuel_type, branch_name, rc, solar, full in candidates[:8]:
        s_days, s_avg, s_med = solar
        f_days, f_avg, f_med = full
        print(
            f"- {dev_id} | {dev_name} | fuel={fuel_type} | branch={branch_name} | readings={rc:,} | "
            f"solar_avg={s_avg or 0:,.2f} kWh/day | full_avg={f_avg or 0:,.2f} kWh/day"
        )

    # Prefer UTILITY / grid-looking device as the primary meter for bill-based sizing.
    primary = next((c for c in candidates if looks_like_grid(c[1])), candidates[0])
    dev_id, dev_name, fuel_type, branch_name, rc, solar, full = primary
    s_days, s_avg, s_med = solar
    f_days, f_avg, f_med = full

    # PV sizing (PV-only) for 60% of solar-hours energy
    target_kwh_day = (s_avg or 0) * 0.60
    kWp = target_kwh_day / (PSH * PR) if PSH * PR else 0
    # round up to nearest 5kWp
    kWp_rounded = int(((kWp + 4.999) // 5) * 5) if kWp > 0 else 0

    annual_kwh = target_kwh_day * 365
    annual_savings = annual_kwh * TARIFF_NGN_PER_KWH

    print("\nAssuming PV-only (no battery), sized to offset 60% of SOLAR-HOURS energy:")
    print(f"Primary meter used: {dev_name} (device_id={dev_id})")
    print(f"Solar-hours avg: {s_avg:,.2f} kWh/day (9:00-16:30)")
    print(f"Target (60%): {target_kwh_day:,.2f} kWh/day")
    print(f"Sizing assumptions: PSH={PSH}h/day, PR={PR}")
    print(f"Required PV size: {kWp:,.1f} kWp  (rounded recommendation: {kWp_rounded} kWp)")
    print(f"Annual offset energy: {annual_kwh:,.0f} kWh/year")
    print(f"Annual savings @ ₦{TARIFF_NGN_PER_KWH}/kWh: ₦{annual_savings:,.0f}/year")

    if f_avg and s_avg:
        max_bill_offset_no_battery = min(1.0, s_avg / f_avg)
        print(
            f"\nNote: PV-only maximum bill offset (without storage/net-metering) is limited by daytime share: "
            f"~{max_bill_offset_no_battery*100:,.1f}% of total kWh (based on last-{MONTHS_BACK}mo averages)."
        )

    conn.close()


if __name__ == "__main__":
    main()

