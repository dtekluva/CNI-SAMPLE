# Proposal: Solar + Battery Microgrid for Ecobank — ELF Branch

**Client:** Ecobank (client_id: 29)  
**Site:** Eco Bank ELF Branch (branch_id: 87)  
**Objective:** Cut diesel + grid spend, improve uptime, and stabilize power quality by placing the **whole branch load behind a 3‑phase hybrid PCS/inverter** blending **Solar + Battery + Grid + Generator**.

---

## 1) Executive Summary (Compelling Offer)
Ecobank ELF is an excellent candidate for solar because:
- The branch has **strong daytime energy use** (very low risk of PV wastage).
- The site runs **a lot of generator**, even during daytime—so each solar kWh offsets **high‑cost diesel**.

**Recommendation (best ROI):** deploy **~80 kWp PV + 100 kW hybrid PCS** now (fastest payback).  
**Upgrade path:** add **100 kWh battery** when you want resilience / night diesel reduction.

---

## 2) What the Meter Data Says (Last 12 Months)
Analysis window: trailing 12 months (anchored to latest reading on **2026‑01‑21**), Lagos time.

### 2.1 Energy (kWh)
- **Average site energy:** **~519 kWh/day**
  - **Daytime (09:00–16:30): ~266 kWh/day**
  - **Night/other hours: ~253 kWh/day**

**Totals over period:** **174,463 kWh**
- **Generator:** **88,904 kWh** (~51%)
- **Utility/grid:** **85,559 kWh** (~49%)

### 2.2 Demand (kW)
For reliable design, we used percentiles (not raw spikes):
- Utility meter: **p99 ≈ 83 kW**, max observed ≈ 96 kW

**Hybrid PCS sizing:** **100 kW, 3‑phase** (covers observed peaks with margin).

---

## 3) System Architecture (Whole‑Load Through the PCS)
**Single protected bus:** all branch loads are fed from the hybrid PCS output.

Operating logic:
1) Solar serves load first
2) Excess solar charges battery (if present)
3) PCS imports from grid when needed
4) During grid outages, PCS accepts/starts generator and blends seamlessly

**Must‑have electrical scope:** maintenance bypass, protection coordination, generator interface (anti‑backfeed / reverse power), monitoring + metering.

---

## 4) Recommended Sizing Options
### Option A — PV‑only (best ROI / fastest payback)
- **PCS:** 100 kW hybrid PCS/inverter
- **PV:** **~80 kWp** (≈ **130 × 620W panels**)

### Option C — PV + 100 kWh battery (resilience + night diesel reduction)
- Same PV/PCS as Option A
- **Battery:** **100 kWh nominal**
- Estimated battery night delivery from PV surplus: **~30 kWh/day**

### Option B — Deeper offset (higher savings, slower payback)
- **PV:** **~100 kWp** (≈ **162 × 620W panels**)
- **Battery:** **~200 kWh nominal**
- Target: ~70% energy offset (energy-basis)

---

## 5) Financial Model (ROI / Payback)
### 5.1 Energy value used (measured blend)
Based on measured generator vs utility shares:
- **Day avoided-cost:** **~₦282/kWh**
- **Night avoided-cost:** **~₦258/kWh**

### 5.2 PV yield basis
- **PSH = 5.0**, **PR = 0.75**  
- Expected yield ≈ **1,369 kWh/kWp/year**

---

## 6) CAPEX Breakdown (Benchmarks Provided; BOS/Installation Excluded)
**Unit costs used:** PCS **₦15.0m**; panels **₦150k/panel (620W)**; battery **₦19.2m per 60 kWh** (≈ **₦320k/kWh**).

### 6.1 Option A CAPEX (PV‑only)
- PCS (100 kW): **₦15,000,000**
- Panels: **130 × ₦150,000 = ₦19,500,000**
- **Total CAPEX:** **₦34,500,000**

### 6.2 Option C CAPEX (PV + 100 kWh)
- PCS (100 kW): **₦15,000,000**
- Panels: **₦19,500,000**
- Battery: **100 kWh × ₦320,000/kWh = ₦32,000,000**
- **Total CAPEX:** **₦66,500,000**

### 6.3 Option B CAPEX (PV + 200 kWh)
- PCS (100 kW): **₦15,000,000**
- Panels: **162 × ₦150,000 = ₦24,300,000**
- Battery: **200 kWh × ₦320,000/kWh = ₦64,000,000**
- **Total CAPEX:** **₦103,300,000**

---

## 7) Savings & Payback Summary
| Option | PV | Battery | Annual savings (₦/yr) | CAPEX (₦) | Simple payback |
|---|---:|---:|---:|---:|---:|
| **A (Recommended)** | ~80 kWp | — | **₦27.39m** | **₦34.50m** | **1.26 yrs** |
| C | ~80 kWp | 100 kWh | **₦30.25m** | **₦66.50m** | **2.20 yrs** |
| B | ~100 kWp | 200 kWh | **₦36.54m** | **₦103.30m** | **2.83 yrs** |

**Compelling conclusion:** Option A delivers the fastest payback because daytime demand is high and generator usage is material—solar offsets diesel immediately.

---

## 8) What’s Excluded (to be priced after site survey)
- Mounting/BOS, cabling, combiner boxes, breakers, earthing/lightning
- Switchgear, ATS/generator interface, protection coordination
- Installation labor, civil works, permits, commissioning
- Optional remote monitoring / SLA

---

## 9) Next Steps (Fast Execution)
1) **Site survey (1 day):** roof layout, shading, structural checks, cable routes, generator interface
2) **Final engineering:** single-line, protection, BOS + installation “all‑in” CAPEX
3) **Deployment:** procurement + installation + commissioning

**Approval request:** confirm whether you want **Option A now** with **Option C as the upgrade path**, or proceed directly to a battery-backed option for resilience.

