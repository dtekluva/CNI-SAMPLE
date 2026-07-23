# Build Decisions — CNI Group Governance Portal

**Status:** Partially locked — key calls signed off 2026-07-17 (see "Locked" note below); ◷ rows pending stakeholders
**Prepared:** 2026-07-17

> **Locked 2026-07-17 (CTO sign-off):** **D-A1** stack = Django + DRF + PostgreSQL + React/Vite/TS ✅ · **D-B1** = **Group tree immediately** (multi-entity UI is Phase 1 — overrides the original single-entity-first recommendation) · **D-B9** = Responsive PWA first ✅. All other ✅ rows treated as locked unless objected. See D-B1 for the phasing ripple.
**Purpose:** Lock the decisions the PRD deferred (§22) and choose the stack, so the work can be scaffolded and a build-loop can run against an executable definition-of-done. Approve or override each row; once locked, this file is the source of truth that the task backlog and scaffold are generated from.

**Status legend**
- ✅ **Recommended default** — approve to lock; I can proceed on this without further input.
- ⚑ **Your call** — a product/strategy decision only you should make; I've recommended one.
- ◷ **Needs a stakeholder** — requires Company Secretary / Legal / Brand / Procurement input before it can truly lock; I've proposed a safe interim so the build isn't blocked.

---

## Part A — Architecture & stack (the PRD left this open on purpose)

### D-A1 — Overall stack ✅
**Recommendation:** **Django + Django REST Framework (Python) API · PostgreSQL · React + Vite + TypeScript SPA** consuming the API and rendering the Northstar design system.
**Why:** This is a permissions-, audit-, and admin-heavy product — Django's mature auth, ORM, migrations, signals (for audit logging), and admin scaffold are a direct fit, and it's a stack the team already ships (agency banking, Agamos). React+Vite matches the existing prototypes and the CSS-token design system drops straight in. Postgres gives row-level scoping, JSONB for flexible metadata, and strong integrity constraints.
**Alternatives considered:** Next.js full-stack (loses Django's admin + mature permissions, which are gold here); Django templates + HTMX (simpler, but the rich flows — in-meeting mode, pack reader, follow-the-presenter — want a real frontend framework).

### D-A2 — Database ✅
**Recommendation:** **PostgreSQL 16** as the target DB. SQLite permitted only for fast unit tests; all integration/e2e tests run against Postgres so nothing Postgres-specific slips through.
**Why:** Multi-entity scoping, JSONB metadata, constraints, and the append-only/audit needs all lean on Postgres features.

### D-A3 — Auth & MFA ✅
**Recommendation:** Django auth + **TOTP MFA (django-otp)** mandatory, session timeout, concurrent-session control. **SSO via OIDC** (Google / Microsoft Entra) as an additive option. `[REG:NDPA]`
**Why:** Satisfies NFR-SEC-1 with proven libraries; SSO fits directors who live in Google/Microsoft.

### D-A4 — Background jobs ✅
**Recommendation:** **Celery + Redis** for reminder cascades, compliance-deadline nudges, pack compilation, and cron-style jobs.
**Note:** On the 1 GB dev box this is heavy (see D-A8). Fine for production; for dev we can run the worker on-demand.

### D-A5 — File / document storage ✅
**Recommendation:** **S3-compatible object storage** (DigitalOcean Spaces or AWS S3), server-side encryption, signed short-lived URLs, never public. Server-side PDF pipeline for pack compilation + per-viewer watermarking.
**Why:** Satisfies FR-DOC-3 (watermark/download control) and NFR-SEC-2 (encryption at rest).

### D-A6 — Test harness = the loop's definition-of-done ✅ (critical)
**Recommendation:** **pytest + pytest-django** (backend), **Vitest + React Testing Library** (frontend), **Playwright** (end-to-end). Every FR story's Given/When/Then criteria are authored as automated tests; **the build-loop only advances a task when its tests are green.**
**Why:** This is what turns "build exhaustively in a loop" from drift into discipline — the GWT criteria become the executable acceptance gate.

### D-A7 — Local/dev deployment ✅
**Recommendation:** **Docker Compose** on the box (services: postgres, redis, api, web) bound to `127.0.0.1`; report the web port to the team per ACCESS.md. Production networking/TLS handled by the team later.
**Why:** Reproducible, matches the "build on the box, report the port" handoff.

### D-A8 — Dev-box sizing ✅ RESOLVED
**Done (2026-07-17):** `libertyapp-01` resized to **s-2vcpu-2gb** — 2 vCPU / 2 GB RAM / 60 GB disk (58 GB usable, root FS auto-expanded). Confirmed on box. Comfortable for Postgres + Redis + API + Vite together. 2 GB swap retained.

---

## Part B — The §22 open questions

### D-B1 — Entity scope at launch ✅ LOCKED = Group tree immediately
**Question:** Single-entity UI first, or expose the group tree immediately?
**Decision (CTO, 2026-07-17):** **Group tree immediately** — multi-entity navigation (entity switcher, group vs entity views) ships in **Phase 1**, not Phase 2.
**Phasing ripple (must reflect in the backlog + PRD rollout):**
- **FR-ENT-2** (group vs entity views) and the **entity switcher / group dashboard** move **Phase 2 → Phase 1**.
- RBAC must resolve **group-level roles vs entity-scoped roles** from the first release (FR-RBAC-1), so permission scoping is exercised on real hierarchy immediately.
- We need the **real CNI entity hierarchy** (holdco + subsidiaries, CAC RC numbers) early to seed FR-ENT-1 — this becomes a stakeholder input (cosec/company info).
- Higher up-front UI complexity accepted in exchange for a true group product from launch.

### D-B2 — Secure director-to-director messaging ⚑
**Recommendation:** **Off by default** (feature-flagged off). Revisit only if the board explicitly wants it.
**Why:** Legal-discoverability risk; most boards keep governance discussion in minutes/resolutions, not a chat.

### D-B3 — Data residency (production) ◷ `[REG:NDPA]`
**Recommendation:** Build **residency-agnostic** (config-driven). For **production**, plan **Nigeria/region hosting or an NDPA-compliant provider under a DPA**, given CBN/NDPA sensitivity. Dev can run on the current offshore box.
**Why:** NDPA + CBN expectations make production data locality a real question that Legal should confirm. Building config-driven means the decision doesn't block engineering.

### D-B4 — E-signature ◷
**Recommendation:** **Integrate, don't build** — evaluate **DocuSign** first (Adobe Acrobat Sign as alternate). Native/crypto signing is out of scope.
**Why:** Legal weight and non-repudiation come from an established provider; building signing ourselves is risk we don't need. Procurement/Legal to pick the vendor.

### D-B5 — Statutory notice periods ◷ `[REG:CAMA]`
**Recommendation:** Make notice periods **configurable per meeting type per entity**; seed with CAMA defaults **to be confirmed by the Company Secretary**. Do **not** hardcode guessed values.
**Why:** The exact statutory rules must come from the cosec/articles; config + seed lets us build now and correct the values on confirmation.

### D-B6 — Numbering schemes ◷
**Recommendation:** **Configurable per entity**; seed a default pattern `‹ENTITY›/‹BODY›/‹YEAR›/‹SEQ›` (e.g. `CNI/BD/2026/014`), confirm the convention with the cosec.

### D-B7 — CAC filing ✅
**Recommendation:** **Track-only** (prepare + track filings and evidence); **no direct CAC integration** initially. Revisit as a Phase 3 integration.

### D-B8 — AI-assist timing ✅
**Recommendation:** **Hold the AI features for Phase 3** (per the PRD's "AI is last on purpose"), but keep the design hooks (AI Insight component, purple tokens) and the NFR-AI guardrails in from the start so nothing has to be retrofitted.

### D-B9 — Mobile ✅ LOCKED = PWA-first
**Decision (CTO, 2026-07-17):** **Responsive PWA first** (installable, offline pack reading via service worker + encrypted local cache). Native iOS/Android deferred to Phase 3, and only if biometric/secure-storage requirements force it.
**Why:** One codebase, faster, and a PWA covers offline reading + install. Native is a big cost we can defer.

### D-B10 — Delegation of Authority (DoA) matrix ◷
**Recommendation:** **Design it here** as a configurable table (role/body × approval type × naira limit); seed from whatever CNI already uses. Needs the actual authority limits from Finance/cosec to populate.

---

## Part C — Design-system decisions

### D-C1 — Typeface ⚑
**Recommendation:** **Inter** (UI) + Source Serif 4 (reading) + JetBrains Mono (IDs/figures), as proposed in the tokens. Swap only if CNI has a licensed brand typeface.

### D-C2 — Primary brand hue ◷
**Recommendation:** Keep the tokens' confident blue `#2563EB` **unless CNI Group has a brand color** — if so, give me the hex and I retarget `color.primary` + the neutral tint in one change.

### D-C3 — Density ✅
**Recommendation:** Ship the **comfortable default** (16 px body) plus a **compact density mode** for data-dense screens (audit log, registers, resolution list). Add to component roadmap.

---

## Part D — Loop-enablement decisions

### D-D1 — Loop scope ✅
**Recommendation:** Run the build-loop over **Phase 1 breadth** (the MVP spine) first, task-by-task, each gated on green tests (D-A6). Phases 2–3 follow once Phase 1 is solid.

### D-D2 — Human checkpoints (not everything loops) ✅
**Recommendation:** Mark **security/permissions/audit/AI** tasks as **human-review checkpoints** — the loop builds and tests them, but a human signs off before they're considered done. These are the "wrong-but-plausible is dangerous" areas.

### D-D3 — Source of truth for the loop ✅
**Recommendation:** Generate a **dependency-ordered task backlog** (data model → auth/RBAC → entity CRUD → meetings → packs → minutes → resolutions → …), each task carrying its FR/NFR ID, its GWT-derived tests, and its checkpoint flag. The loop reads this backlog, builds, tests, and advances.

### D-D4 — Irreversible/external actions stay manual ✅
**Recommendation:** The loop never performs irreversible or external actions autonomously (deploys, sending real notifications, e-sign calls, data deletion). Those remain human-gated, consistent with the product's own safety posture.

---

## Sign-off checklist

**Locked (CTO, 2026-07-17):** D-A1 (stack), D-B1 (group tree immediately), D-B9 (PWA-first), plus all ✅ rows: D-A2…A7, D-B7, D-B8, D-C3, D-D1…D4.

**Still open:**
- **⚑ your call (low stakes; safe defaults in place):** **D-B2** (messaging off by default), **D-C1** (Inter typeface). Say the word to change; otherwise they stand.
- **◷ needs a stakeholder** — please route or give me the answer: **D-A8** (dev-box size), **D-B3** (prod residency / Legal), **D-B4** (e-sign vendor / Procurement), **D-B5** (notice periods / cosec), **D-B6** (numbering / cosec), **D-B10** (DoA limits / Finance), **D-C2** (brand hue / Brand), and the **real CNI entity hierarchy** to seed FR-ENT-1 (now needed early because of D-B1).

The locked rows are enough to scaffold the repo + test harness on the box and generate the dependency-ordered task backlog. The ◷ rows fill in as stakeholders respond, without blocking the build.
