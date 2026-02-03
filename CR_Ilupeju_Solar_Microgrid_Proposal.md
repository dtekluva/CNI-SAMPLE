# Proposal: Solar + Battery Microgrid for Chicken Republic (CR_Ilupeju)

**Prepared for:** Chicken Republic — **CR_Ilupeju (branch_id: 83)**  
**Objective:** Reduce grid + diesel spend, improve uptime, and stabilize power quality by placing the **entire branch load behind a hybrid inverter/PCS** that blends **Solar + Battery + Grid + Generator**.

---

## 1) Executive Summary (The Offer)
We propose a **whole-site, inverter-backed microgrid** for CR_Ilupeju built around a **100 kW hybrid PCS**.

**Two options (same architecture, different PV size):**
- **Option 1 — Roof PV (base):** **~40.3 kWp** (65 × 620 W panels)
- **Option 2 — Roof PV + Carport PV (upgrade):** **~65.1 kWp** (105 × 620 W panels total)

**Financial headline (using your energy costs):**
- Energy prices used: **Grid ₦230/kWh**, **Generator ₦309/kWh**
- Indicative payback (using provided component CAPEX only):
  - **Without carport:** ~**3.26 years**
  - **With carport:** ~**2.57 years**

---

## 2) What the Data Says (GEN + UTILITY only)
From the last 12 months of CR_Ilupeju readings:
- **Annual energy:** **~215,634 kWh/year** (≈ **606 kWh/day**)
- **Average load (energy-based):** **~25 kW**
- **Peak observed demand:** **~83 kW**
- Supply mix:
  - **Grid (UTILITY):** ~**183,496 kWh/year**
  - **Generator:** ~**32,138 kWh/year** (generator operated on ~250 days)

This profile is ideal for solar because daytime demand is strong (little PV wastage) and generator usage is material (diesel savings upside).

---

## 3) System Architecture (Whole-load Through the Inverter)
**Single protected bus:** all branch loads are fed from the hybrid PCS output.

**How it works:**
- Solar serves load first; surplus charges battery
- Battery supports load during dips/changeovers
- PCS imports from grid when needed; when grid is unavailable, PCS accepts/starts generator
- PCS controls blending to avoid reverse power into generator and smooth transients

**Must-have electrical scope:** maintenance bypass, protection coordination, proper generator interface (anti-backfeed / reverse power), metering + monitoring.

---

## 4) Recommended Sizing
### 4.1 Hybrid inverter/PCS
- **100 kW 3-phase hybrid PCS** (whole-load rating)
  - Sized above the measured **~83 kW** peak with margin

### 4.2 Battery (recommended)
- **60 kWh LFP** (best balance of ROI + operational value)
  - Seamless transfer support, stability for cold room loads, generator smoothing

### 4.3 Solar PV (two options)
- **Option 1 (no carport):** 65 panels × 620 W = **40.3 kWp**
- **Option 2 (with carport):** (65 + 40) panels × 620 W = **65.1 kWp**

---

## 5) Expected Energy & Savings
### 5.1 PV production assumption
- Lagos yield model: **PSH = 5.0**, **PR = 0.75**
- Expected yield ≈ **1,369 kWh/kWp/year**

### 5.2 Expected PV energy
- **Option 1 (40.3 kWp):** ~**55,171 kWh/year**
- **Option 2 (65.1 kWp):** ~**89,122 kWh/year**

### 5.3 Value of energy avoided
We value each solar kWh using a blended avoided-cost basis reflecting daytime grid/gen usage:
- **Blended avoided cost ≈ ₦244/kWh** (grid ₦230, generator ₦309)

**Estimated annual savings:**
- **Option 1:** 55,171 × 244 ≈ **₦13.46m/year**
- **Option 2:** 89,122 × 244 ≈ **₦21.75m/year**

---

## 6) ROI / Payback (Using Your CAPEX Benchmarks)
> Note: CAPEX below includes **PCS + battery + panels (+ carport)** as provided. BOS/installation/protection can be added after site survey for an “all-in” ROI.

### 6.1 CAPEX
| Item | Without Carport | With Carport |
|---|---:|---:|
| Hybrid PCS (100 kW) | ₦15.00m | ₦15.00m |
| Battery (60 kWh LFP) | ₦19.20m | ₦19.20m |
| Panels (₦150k each) | 65 panels = **₦9.75m** | 105 panels = **₦15.75m** |
| Carport structure | — | **₦6.00m** |
| **Total CAPEX** | **₦43.95m** | **₦55.95m** |

### 6.2 Payback
- **Without carport:** 43.95 / 13.46 ≈ **3.26 years**
- **With carport:** 55.95 / 21.75 ≈ **2.57 years**

### 6.3 Carport upgrade economics (incremental)
- Incremental cost (carport + 40 panels): **₦12.0m**
- Incremental savings: (89,122 − 55,171) × 244 ≈ **₦8.28m/year**
- **Incremental payback:** 12.0 / 8.28 ≈ **1.45 years**

---

## 7) What CR_Ilupeju Gets (Beyond Savings)
- **Lower diesel exposure:** PV continues producing even when the branch is on generator (blended operation)
- **Higher uptime + better power quality:** inverter-backed bus stabilizes voltage/frequency for sensitive loads
- **Reduced generator wear:** fewer starts, better loading, lower maintenance burden
- **Remote monitoring & reporting:** visibility for performance, alarms, and energy KPIs

---

## 8) Key Assumptions (For This Financial Model)
- Energy prices: **Grid ₦230/kWh**, **Generator ₦309/kWh**
- PV yield basis: **PSH 5.0**, **PR 0.75** (~1,369 kWh/kWp/year)
- Solar energy is assumed to be largely self-consumed due to strong daytime demand
- CAPEX table includes only items explicitly provided (PCS, battery, panels, and carport)

---

## 9) Next Steps
1) Site survey (DB capacity, protection, earthing, space confirmation, cable routes)
2) Confirm coupling approach for PV expansion (DC-coupled vs AC-coupled) and finalize SLD
3) Finalize BOS + installation cost and lock the “all-in” ROI and delivery schedule

**We recommend proceeding with Option 1 immediately, and treating the carport PV as a high-ROI upgrade path (≈1.45-year incremental payback).**

