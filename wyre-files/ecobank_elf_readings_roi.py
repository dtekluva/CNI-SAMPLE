#!/usr/bin/env python3
"""Ecobank ELF (branch_id=87): summarize meter readings + quick ROI sizing (no solar telemetry).

- Pulls candidate UTILITY/GEN meters for the branch.
- Computes trailing energy (kWh/day) for full-day + solar window (09:00-16:30 Lagos).
- Computes per-meter power stats (kW).
- Produces 2 quick sizing/ROI options:
  * PV-only sized to self-consume daytime energy
  * Hybrid PV+storage sized to offset TARGET_OFFSET of total energy

Assumptions mirror earlier proposal benchmarks (edit constants below as needed).
"""

import math
import os
from typing import Optional, Tuple

import psycopg2

BRANCH_ID = 87
CLIENT_ID = 29
TZ = "Africa/Lagos"
MONTHS_BACK = 12
SOLAR_START = "09:00:00"
SOLAR_END = "16:30:00"

# Financial assumptions (benchmarks used previously)
GRID_NGN_PER_KWH = 230
GEN_NGN_PER_KWH = 309

PCS_COST_NGN = 15_000_000
PANEL_COST_NGN = 150_000
PANEL_WATT_W = 620
BATTERY_COST_60KWH_NGN = 19_200_000

PSH = 5.0
PR = 0.75
BAT_RTE = 0.90
BAT_DOD = 0.80
BAT_EOL = 0.80
TARGET_OFFSET = 0.70


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
    if looks_like_grid(name):
        return "UTILITY"
    if (fuel_type or "").upper() in {"DIESEL", "PETROL", "GAS"}:
        return "GEN"
    if looks_like_gen(name):
        return "GEN"
    return "OTHER"


def round_up(x: float, step: float) -> float:
    if x <= 0:
        return 0
    return step * math.ceil(x / step)


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
        "SELECT id,name,address,utility_tariff,is_active,client_id FROM main_branch WHERE id=%s",
        (BRANCH_ID,),
    )
    print("BRANCH:", cur.fetchone())

    cur.execute(
        """
        SELECT id,name,device_id,fuel_type,is_active
        FROM main_device
        WHERE branch_id=%s
        ORDER BY is_active DESC, id;
        """,
        (BRANCH_ID,),
    )
    devices = cur.fetchall()
    if not devices:
        print("No devices found for branch_id.")
        conn.close()
        return

    active = [(d_id, nm, serial, fuel) for (d_id, nm, serial, fuel, act) in devices if act]
    if not active:
        print("No ACTIVE devices for this branch.")
        conn.close()
        return

    dev_ids = [d[0] for d in active]

    cur.execute("SELECT MAX(post_datetime) FROM main_reading WHERE device_id = ANY(%s)", (dev_ids,))
    anchor = cur.fetchone()[0]
    print("ANCHOR_TS_UTC:", anchor)
    if not anchor:
        print("No readings found for active branch devices.")
        conn.close()
        return

    # reading counts within trailing window anchored to latest reading
    cur.execute(
        """
        SELECT device_id, count(*)
        FROM main_reading
        WHERE device_id = ANY(%s)
          AND post_datetime >= (%s - (%s || ' months')::interval)
        GROUP BY device_id;
        """,
        (dev_ids, anchor, MONTHS_BACK),
    )
    counts = dict(cur.fetchall())

    candidates = []
    for dev_id, name, serial, fuel in active:
        role = classify_role(name, fuel)
        candidates.append((dev_id, name, serial, fuel, role, counts.get(dev_id, 0)))

    print("\nDEVICES (active):")
    for dev_id, name, serial, fuel, role, cnt in sorted(candidates, key=lambda r: (-r[5], r[0])):
        print(f"- {dev_id} | {name} | role={role} | fuel={fuel or 'N/A'} | serial={serial} | samples={cnt:,}")

    supply = [c for c in candidates if c[4] in {"UTILITY", "GEN"} and c[5] > 0]
    if not supply:
        supply = [c for c in sorted(candidates, key=lambda r: -r[5])[:5] if c[5] > 0]

    sel_ids = [c[0] for c in supply]
    gen_ids = [c[0] for c in supply if c[4] == "GEN"]
    util_ids = [c[0] for c in supply if c[4] == "UTILITY"]

    print(f"\nSELECTED_METERS (n={len(sel_ids)}): {sel_ids} | GEN={gen_ids} | UTILITY={util_ids}")

    cur.execute(
        f"""
        WITH r AS (
          SELECT device_id,
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
            MAX(kwh_import) AS max_kwh,
            MIN(kwh_import) FILTER (WHERE local_ts::time >= time %s AND local_ts::time <= time %s) AS min_kwh_solar,
            MAX(kwh_import) FILTER (WHERE local_ts::time >= time %s AND local_ts::time <= time %s) AS max_kwh_solar
          FROM r
          GROUP BY device_id, date(local_ts)
        ), daily_clean AS (
          SELECT
            device_id,
            day,
            GREATEST(0, max_kwh-min_kwh) AS kwh_day,
            GREATEST(0, COALESCE(max_kwh_solar,0)-COALESCE(min_kwh_solar,0)) AS kwh_solar
          FROM daily
          WHERE (max_kwh-min_kwh) > 0
        ), combined AS (
          SELECT
            day,
            SUM(kwh_day) AS kwh_day,
            SUM(kwh_solar) AS kwh_solar,
            COALESCE(SUM(kwh_day) FILTER (WHERE device_id = ANY(%s)), 0) AS kwh_day_gen,
            COALESCE(SUM(kwh_solar) FILTER (WHERE device_id = ANY(%s)), 0) AS kwh_solar_gen,
            COALESCE(SUM(kwh_day) FILTER (WHERE device_id = ANY(%s)), 0) AS kwh_day_util,
            COALESCE(SUM(kwh_solar) FILTER (WHERE device_id = ANY(%s)), 0) AS kwh_solar_util
          FROM daily_clean
          GROUP BY day
        )
        SELECT
          COUNT(*) AS days,
          SUM(kwh_day) AS sum_kwh_day,
          SUM(kwh_solar) AS sum_kwh_solar,
          SUM(kwh_day_gen) AS sum_kwh_day_gen,
          SUM(kwh_solar_gen) AS sum_kwh_solar_gen,
          SUM(kwh_day_util) AS sum_kwh_day_util,
          SUM(kwh_solar_util) AS sum_kwh_solar_util
        FROM combined;
        """,
        (TZ, sel_ids, anchor, MONTHS_BACK, SOLAR_START, SOLAR_END, SOLAR_START, SOLAR_END, gen_ids or [0], gen_ids or [0], util_ids or [0], util_ids or [0]),
    )

    (
        days,
        sum_day,
        sum_solar,
        sum_day_gen,
        sum_solar_gen,
        sum_day_util,
        sum_solar_util,
    ) = cur.fetchone()

    days = int(days or 0)
    avg_day = (sum_day or 0) / days if days else 0.0
    avg_solar = (sum_solar or 0) / days if days else 0.0
    avg_day_gen = (sum_day_gen or 0) / days if days else 0.0
    avg_solar_gen = (sum_solar_gen or 0) / days if days else 0.0
    avg_day_util = (sum_day_util or 0) / days if days else 0.0
    avg_solar_util = (sum_solar_util or 0) / days if days else 0.0

    avg_night = (avg_day or 0) - (avg_solar or 0)
    night_gen = (avg_day_gen or 0) - (avg_solar_gen or 0)
    night_util = (avg_day_util or 0) - (avg_solar_util or 0)

    print("\nENERGY (kWh/day averages across days):")
    print(f"- Days with data: {days}")
    print(f"- Total avg: {avg_day or 0:,.2f} | Solar-window avg: {avg_solar or 0:,.2f} | Night/other avg: {avg_night:,.2f}")
    print(f"- GEN avg: total={avg_day_gen or 0:,.2f} | solar={avg_solar_gen or 0:,.2f} | night={night_gen:,.2f}")
    print(f"- UTILITY avg: total={avg_day_util or 0:,.2f} | solar={avg_solar_util or 0:,.2f} | night={night_util:,.2f}")

    print("\nENERGY (totals over trailing window):")
    print(f"- Total: {sum_day or 0:,.0f} kWh | Solar-window: {sum_solar or 0:,.0f} kWh")
    print(f"- GEN: {sum_day_gen or 0:,.0f} kWh (solar {sum_solar_gen or 0:,.0f})")
    print(f"- UTILITY: {sum_day_util or 0:,.0f} kWh (solar {sum_solar_util or 0:,.0f})")

    def blend(gen_kwh: float, util_kwh: float) -> float:
        tot = (gen_kwh or 0) + (util_kwh or 0)
        if tot <= 0:
            return GRID_NGN_PER_KWH
        return (gen_kwh / tot) * GEN_NGN_PER_KWH + (util_kwh / tot) * GRID_NGN_PER_KWH

    # Use totals (same denominator) to compute blended avoided-cost values.
    sum_night_gen = (sum_day_gen or 0) - (sum_solar_gen or 0)
    sum_night_util = (sum_day_util or 0) - (sum_solar_util or 0)
    v_day = blend(sum_solar_gen or 0, sum_solar_util or 0)
    v_night = blend(sum_night_gen, sum_night_util)

    # Option A: PV-only sized to self-consume daytime energy
    pv_kwp_a = (avg_solar or 0) / (PSH * PR) if (PSH * PR) else 0
    pv_kwp_a = round_up(pv_kwp_a, 10)
    panels_a = math.ceil((pv_kwp_a * 1000) / PANEL_WATT_W) if pv_kwp_a else 0
    annual_gen_a = pv_kwp_a * PSH * PR * 365
    annual_used_a = min(annual_gen_a, (avg_solar or 0) * 365)
    annual_save_a = annual_used_a * v_day
    capex_a = PCS_COST_NGN + panels_a * PANEL_COST_NGN
    payback_a = (capex_a / annual_save_a) if annual_save_a > 0 else 0

    # Option C: PV-only + small battery to capture surplus PV (buffering / limited night offset)
    batt_nom_c = 100.0  # kWh nominal
    pv_daily_gen_a = pv_kwp_a * PSH * PR
    direct_day_c = min(avg_solar or 0, pv_daily_gen_a)
    surplus_day_c = max(0.0, pv_daily_gen_a - direct_day_c)
    batt_delivered_c = min(surplus_day_c * BAT_RTE, batt_nom_c * BAT_DOD)
    batt_cost_c = (batt_nom_c / 60.0) * BATTERY_COST_60KWH_NGN
    annual_save_c = (direct_day_c * 365 * v_day) + (batt_delivered_c * 365 * v_night)
    capex_c = PCS_COST_NGN + panels_a * PANEL_COST_NGN + batt_cost_c
    payback_c = (capex_c / annual_save_c) if annual_save_c > 0 else 0

    # Option B: PV + storage sized to offset TARGET_OFFSET of total energy
    target_kwh = (avg_day or 0) * TARGET_OFFSET
    direct_kwh = min(avg_solar or 0, target_kwh)
    batt_delivered = max(0.0, target_kwh - direct_kwh)
    pv_kwh_needed = direct_kwh + (batt_delivered / BAT_RTE if BAT_RTE else 0)
    pv_kwp_b = pv_kwh_needed / (PSH * PR) if (PSH * PR) else 0
    pv_kwp_b = round_up(pv_kwp_b, 10)
    batt_nom = batt_delivered / (BAT_DOD * BAT_EOL) if (BAT_DOD * BAT_EOL) else 0
    batt_nom = round_up(batt_nom, 50)

    panels_b = math.ceil((pv_kwp_b * 1000) / PANEL_WATT_W) if pv_kwp_b else 0
    batt_cost_b = (batt_nom / 60.0) * BATTERY_COST_60KWH_NGN
    capex_b = PCS_COST_NGN + panels_b * PANEL_COST_NGN + batt_cost_b
    annual_save_b = (direct_kwh * 365 * v_day) + (batt_delivered * 365 * v_night)
    payback_b = (capex_b / annual_save_b) if annual_save_b > 0 else 0

    print("\nPOWER (kW) stats per selected meter:")
    cur.execute(
        """
        WITH r AS (
          SELECT device_id, total_kw
          FROM main_reading
          WHERE device_id = ANY(%s)
            AND total_kw IS NOT NULL
            AND post_datetime >= (%s - (%s || ' months')::interval)
        )
        SELECT device_id,
               percentile_cont(0.5) within group (order by total_kw) AS p50,
               percentile_cont(0.9) within group (order by total_kw) AS p90,
               percentile_cont(0.95) within group (order by total_kw) AS p95,
               percentile_cont(0.99) within group (order by total_kw) AS p99,
               MAX(total_kw) AS mx
        FROM r
        GROUP BY device_id
        ORDER BY device_id;
        """,
        (sel_ids, anchor, MONTHS_BACK),
    )
    for dev_id, p50, p90, p95, p99, mx in cur.fetchall():
        nm = next((c[1] for c in supply if c[0] == dev_id), str(dev_id))
        print(
            f"- {dev_id} ({nm}): p50={p50 or 0:,.1f} | p90={p90 or 0:,.1f} | p95={p95 or 0:,.1f} | p99={p99 or 0:,.1f} | max(raw)={mx or 0:,.1f}"
        )

    print("\n--- QUICK ROI OPTIONS (benchmarks; BOS/installation excluded) ---")
    print(f"Avoided-cost value used (day): ₦{v_day:,.0f}/kWh | (night): ₦{v_night:,.0f}/kWh")

    print("\nOption A (PV-only; maximize self-consumption):")
    print(f"- PV: ~{pv_kwp_a:,.0f} kWp (~{panels_a} panels @ {PANEL_WATT_W}W)")
    print(f"- Annual utilized PV energy: {annual_used_a:,.0f} kWh/yr")
    print(f"- Annual savings: ₦{annual_save_a:,.0f}/yr")
    print(f"- CAPEX: ₦{capex_a:,.0f} => Simple payback: {payback_a:,.2f} years")

    print("\nOption C (PV + 100 kWh battery; capture surplus PV for night use):")
    print(f"- PV: ~{pv_kwp_a:,.0f} kWp (~{panels_a} panels)")
    print(f"- Battery: ~{batt_nom_c:,.0f} kWh nominal")
    print(f"- Estimated PV surplus available to charge battery: {surplus_day_c:,.2f} kWh/day")
    print(f"- Estimated battery energy delivered at night: {batt_delivered_c:,.2f} kWh/day")
    print(f"- Annual savings: ₦{annual_save_c:,.0f}/yr")
    print(f"- CAPEX: ₦{capex_c:,.0f} => Simple payback: {payback_c:,.2f} years")

    print("\nOption B (Hybrid PV + storage; target 70% energy offset):")
    print(f"- PV: ~{pv_kwp_b:,.0f} kWp (~{panels_b} panels)")
    print(f"- Battery: ~{batt_nom:,.0f} kWh nominal")
    print(f"- Annual savings: ₦{annual_save_b:,.0f}/yr")
    print(f"- CAPEX: ₦{capex_b:,.0f} => Simple payback: {payback_b:,.2f} years")

    conn.close()


if __name__ == "__main__":
    main()

