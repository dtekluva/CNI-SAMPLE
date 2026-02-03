#!/usr/bin/env python3
"""Check whether daytime demand is limiting PV usage (client_id=4 / Etti).

We originally intended to use stationtelemetry irradiance, but the exported
`irradiate_intensity` column is empty for the last-30-days sample. So this script
uses a pragmatic proxy:

- Focus on *daytime* samples (Africa/Lagos) and define "high sun" as the top 10%
  of station `generation_power` during daytime.
- Look for periods where SOC is already very high (battery "full") and charge
  power is ~0 while generation is small/close to consumption. In a zero-export
  configuration, that combination is consistent with PV curtailment because there
  is no sink (load + allowed battery charge).

Note: without irradiance, we can’t prove curtailment (clouds can also reduce
generation). We can only provide evidence consistent with curtailment.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = "wyre-files/output/etti_solar_telemetry"
TZ = ZoneInfo("Africa/Lagos")


def pct(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return float("nan")
    k = (len(sorted_vals) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(sorted_vals[int(k)])
    return float(sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f))


@dataclass
class Row:
    ts_local: datetime
    gen: float
    cons: float
    chg: float  # signed in export (negative often indicates charging)
    soc: float


def main() -> None:
    rows: list[Row] = []
    with open(f"{BASE}/stationtelemetry_raw_last_30d.csv") as f:
        r = csv.DictReader(f)
        for row in r:
            ts = row.get("timestamp")
            if not ts:
                continue
            gen = row.get("generation_power")
            cons = row.get("consumption_power")
            chg = row.get("charge_power")
            soc = row.get("battery_soc")
            if gen in (None, "") or cons in (None, "") or soc in (None, ""):
                continue
            gen_f = float(gen)
            cons_f = float(cons)
            chg_f = float(chg) if chg not in (None, "") else 0.0
            soc_f = float(soc)
            # export timestamps look like: "2025-12-22 13:30:00+00:00"
            dt_utc = datetime.fromisoformat(ts.replace(" ", "T", 1))
            dt_local = dt_utc.astimezone(TZ)
            rows.append(Row(dt_local, gen_f, cons_f, chg_f, soc_f))

    if not rows:
        print("No usable station telemetry rows found")
        return

    # daytime filter (local)
    day = [x for x in rows if 9 <= x.ts_local.hour <= 16]
    if not day:
        print("No daytime samples found")
        return

    gen_vals_day = sorted([x.gen for x in day])
    gen_p90 = pct(gen_vals_day, 0.90)
    hi = [x for x in day if x.gen >= gen_p90]

    def summarize(label: str, vals: list[float]) -> None:
        vals = sorted(vals)
        if not vals:
            print(f"{label}: no data")
            return
        print(
            f"{label}: n={len(vals)} avg={sum(vals)/len(vals):.2f} p50={pct(vals,0.5):.2f} p90={pct(vals,0.9):.2f} max={vals[-1]:.2f}"
        )

    print(f"Total samples: {len(rows)}")
    print(f"Daytime samples (09:00-16:59): {len(day)}")
    print(f"High-generation threshold (daytime gen p90): {gen_p90:.2f} kW")
    print(f"High-generation samples: {len(hi)}")

    summarize("GEN_kW (all)", [x.gen for x in rows])
    summarize("GEN_kW (day)", [x.gen for x in day])
    summarize("GEN_kW (hi-gen)", [x.gen for x in hi])
    summarize("CONS_kW (hi-gen)", [x.cons for x in hi])
    # charge sign varies; magnitude is what matters for "is it charging hard?"
    summarize("|CHARGE|_kW (hi-gen)", [abs(x.chg) for x in hi])
    summarize("SOC_% (day)", [x.soc for x in day])
    summarize("SOC_% (hi-gen)", [x.soc for x in hi])

    # Curtailment-like condition:
    # during daytime and/or high generation:
    # - SOC is very high (battery basically full)
    # - charge power is ~0 (not absorbing PV)
    # - generation is close to consumption (no export sink)
    curtail = 0
    plateau_50 = 0
    soc95_day = sum(1 for x in day if x.soc >= 95)
    soc98_day = sum(1 for x in day if x.soc >= 98)

    for x in hi:
        if 45 <= x.soc <= 55:
            plateau_50 += 1
        if abs(x.chg) <= 0.5 and x.soc >= 95 and abs(x.gen - x.cons) <= 1.0:
            curtail += 1

    print("")
    print("Signals:")
    print(f" - Daytime SOC>=95%: {100*soc95_day/len(day):.1f}% | SOC>=98%: {100*soc98_day/len(day):.1f}%")
    print(f" - SOC in [45,55]% within hi-gen (possible setpoint plateau): {100*plateau_50/max(len(hi),1):.1f}%")
    print(f" - Curtailment-like within hi-gen (|chg|<=0.5kW, SOC>=95%, |gen-cons|<=1kW): {100*curtail/max(len(hi),1):.1f}%")

    # Charge power ceiling check
    chg_mag_all = sorted([abs(x.chg) for x in rows])
    chg_p95 = pct(chg_mag_all, 0.95)
    chg_p99 = pct(chg_mag_all, 0.99)
    # “ceiling” heuristic: in hi-gen periods, are we frequently at the top-end
    # of observed charge magnitude while SOC is still not nearly full?
    hit_ceiling = sum(1 for x in hi if abs(x.chg) >= max(0.95 * chg_p95, chg_p95 - 0.1) and x.soc <= 90)
    print("")
    print("Charge power limit check:")
    print(f" - |charge_power| p95={chg_p95:.2f} kW | p99={chg_p99:.2f} kW")
    print(f" - hi-irr time near charge ceiling while SOC<=90%: {100*hit_ceiling/max(len(hi),1):.1f}%")


if __name__ == "__main__":
    main()

