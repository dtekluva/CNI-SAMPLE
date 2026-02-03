# Proposal: Solar + Battery Microgrid for Mr Durosinmi Etti (Residence)

**Prepared for:** Mr Durosinmi Etti (**client_id: 4**)  
**Site:** Residence  
**Objective:** Reduce electricity spend, improve uptime, and stabilize power quality by placing the **entire residence load behind a hybrid inverter/PCS** that blends **Solar + Battery + Grid + Generator**.

---

## 1) Executive Summary (The Offer)
We propose a **whole-site, inverter-backed microgrid** sized from the last 12 months of metered consumption.

**Two options (same architecture, different PV size):**
- **Option 1 — Roof PV (base):** **~35.3 kWp** (57 × 620 W panels)
- **Option 2 — Roof PV + Carport PV (upgrade):** **~60.1 kWp** (97 × 620 W panels total)

**Recommended core configuration:**
- **Hybrid PCS/inverter:** sized to cover residence peak demand (recommend **~50 kW class**)
- **Battery:** **~60 kWh LFP** (best ROI + operational value)

**Financial headline (using the same benchmark prices used previously):**
- Energy prices used: **Grid ₦230/kWh**, **Generator ₦309/kWh**
- Indicative payback (PCS + battery + panels (+ carport) only; BOS/installation excluded):
  - **Option 1:** ~**3.9 years** (grid-only value) / **2.9 years** (gen-only value)
  - **Option 2:** ~**3.2–3.6 years** (grid-only, depends on PV self-consumption) / **2.4–2.7 years** (gen-only)

---

## 2) What the Data Says (GEN + UTILITY)
From the trailing 12 months of readings (Africa/Lagos):
- **Utility meter coverage:** 2025-01-11 → 2026-01-21 (87,251 samples)
- **Generator meter present but no usable history** (1 sample only), so the energy breakdown below is **utility-dominated**.

**Trailing-12-month energy (combined meters):**
- **Annual energy:** **~82,059 kWh/year** (≈ **231.15 kWh/day**)
- **Average load (energy-based):** `231.15/24 ≈ 9.6 kW`

**Daytime energy (helps PV + battery design):**
- **07:00–18:00:** **~84.20 kWh/day**
- **09:00–16:30:** **~53.16 kWh/day**

**Power / demand (utility meter):**
- **Peak observed:** **35.6 kW**
- **p95 demand:** **20.2 kW** (typical “high” load)

---

## 3) System Architecture (Whole-load Through the Inverter)
All residence circuits are fed from the **hybrid PCS output** (a single protected bus).

**How it works:**
- Solar serves load first; surplus charges battery
- Battery supports load during dips/changeovers and powers evening/night loads up to its usable capacity
- PCS imports from grid when needed; when grid is unavailable, PCS accepts/starts generator
- PCS controls blending to avoid reverse power into generator and smooth transients

**Must-have electrical scope:** maintenance bypass, protection coordination, proper generator interface (anti-backfeed / reverse power), metering + monitoring.

---

## 4) Recommended Sizing

### 4.1 Hybrid inverter/PCS
- **Recommended PCS class:** **~50 kW** (to sit above the **35.6 kW** observed peak with margin)
  - Final kW/kVA depends on motor starts (e.g., pumps), phase balance, and distribution voltage.

### 4.2 Battery (recommended)
- **60 kWh LFP**
  - Provides meaningful evening/night energy shifting
  - Stabilizes changeovers and reduces generator runtime (where generator is used)

### 4.3 Solar PV (two options)
Sizing logic: design PV to cover daytime consumption and charge ~60 kWh battery for evening use.
- Target PV daily energy ≈ `84.2 (daytime kWh) + ~48 (usable battery kWh)` ≈ **132 kWh/day**

**Option 1 (roof only):**
- 57 panels × 620 W = **35.3 kWp** (≈132 kWh/day modeled)

**Option 2 (roof + carport):**
- (57 + 40) panels × 620 W = **60.1 kWp**
  - Note: this approaches annual energy parity with the site, but **utilization depends heavily on storage/export/load-shifting**.

---

## 5) Expected Energy & Savings

### 5.1 PV production assumption (same model used previously)
- Lagos yield model: **PSH = 5.0**, **PR = 0.75**
- Expected yield ≈ **1,369 kWh/kWp/year**

### 5.2 Expected PV energy
- **Option 1 (35.3 kWp):** ~**48,326 kWh/year**
- **Option 2 (60.1 kWp):** ~**82,277 kWh/year**

### 5.3 Value of energy avoided
Because generator metering is unavailable here, we show a **range**:
- **Grid-only value:** ₦230/kWh (conservative)
- **Gen-only value:** ₦309/kWh (upside if generator regularly supplies the residence)

**Option 1 savings (assumes high self-consumption; PV < annual load):**
- Grid-only: 48,326 × 230 ≈ **₦11.11m/year**
- Gen-only: 48,326 × 309 ≈ **₦14.93m/year**

**Option 2 savings (depends on PV self-consumption):**
If there is no export/net-metering, some PV may be curtailed unless the battery/load can absorb it.
- If **80%** of PV is utilized: 65,822 kWh/yr → **₦15.14m/yr (grid)** to **₦20.34m/yr (gen)**
- If **90%** of PV is utilized: 74,049 kWh/yr → **₦17.03m/yr (grid)** to **₦22.88m/yr (gen)**

---

## 6) ROI / Payback (Using Your Benchmarks)
> Note: CAPEX below includes **PCS + battery + panels (+ carport)** as previously provided. BOS/installation/protection can be added after site survey for an “all-in” ROI.

### 6.1 CAPEX
| Item | Option 1 (No Carport) | Option 2 (With Carport) |
|---|---:|---:|
| Hybrid PCS / inverter system (budget) | ₦15.00m | ₦15.00m |
| Battery (60 kWh LFP) | ₦19.20m | ₦19.20m |
| Panels (₦150k each) | 57 panels = **₦8.55m** | 97 panels = **₦14.55m** |
| Carport structure | — | **₦6.00m** |
| **Total CAPEX** | **₦42.75m** | **₦54.75m** |

### 6.2 Payback
**Option 1:**
- Grid-only: 42.75 / 11.11 ≈ **3.85 years**
- Gen-only: 42.75 / 14.93 ≈ **2.86 years**

**Option 2 (range based on PV utilization):**
- Grid-only: **~3.21–3.61 years**
- Gen-only: **~2.39–2.69 years**

### 6.3 Carport upgrade economics (incremental)
- Incremental cost (carport + 40 panels): **₦12.0m**
- Incremental savings depends on PV utilization:
  - 80% utilization → ~**₦4.02m/year (grid)** → **~3.0-year** incremental payback
  - 90% utilization → ~**₦5.92m/year (grid)** → **~2.0-year** incremental payback

---

## 7) What the Residence Gets (Beyond Savings)
- **Higher uptime and smoother changeovers** (grid ↔ battery ↔ generator)
- **Better power quality** (stable voltage/frequency under inverter control)
- **Lower generator wear** (fewer starts, better loading)
- **Remote monitoring & reporting** (energy KPIs, alerts, performance tracking)

---

## 8) Key Assumptions (For This Financial Model)
- Energy prices: **Grid ₦230/kWh**, **Generator ₦309/kWh**
- PV yield basis: **PSH 5.0**, **PR 0.75** (~1,369 kWh/kWp/year)
- Option 2 explicitly includes a **self-consumption factor (80–90%)** unless export/load-shifting/storage upgrades are confirmed
- CAPEX table includes only items explicitly provided (PCS budget, battery, panels, and carport)
- Generator meter data is currently insufficient; generator savings shown are **scenario-based**, not measured

---

## 9) Next Steps
1) Confirm whether the residence uses generator materially (or provide generator runtime/fuel logs) so we can lock the avoided-cost basis
2) Site survey: DB capacity, phase balance, pump motor starts, earthing, protection, cable routes, PV space confirmation
3) Confirm whether export/net-metering is possible; if not, confirm desired battery size for Option 2 to avoid PV curtailment
4) Finalize BOS + installation cost and lock the “all-in” ROI and delivery schedule

**Recommendation:** Proceed with **Option 1** as the high-confidence, high-utilization design; treat **Option 2** as an upgrade that becomes very attractive when storage or daytime loads (e.g., EV charging) are added.
