# Phase 2 Backlog — Governance Depth

**Status:** In progress
**Prepared:** 2026-07-17
**Branch:** `build/phase-2` (off `build/phase-1`; merges after Phase 1 is reviewed to `main`)
**Sources:** [PRD](reference/PRD_Group_Governance_Portal.md) (all `[Phase 2]` FR/NFR) · Machine-readable driver: [`phase2_backlog.yaml`](phase2_backlog.yaml)

Phase 1 delivered the operating spine (meetings → packs → minutes → resolutions → actions, with RBAC, MFA, audit). **Phase 2 adds the statutory/governance depth** that makes the portal a system of record: registers, directors' interests & conflicts, recusal-aware voting, an immutable minute book, committees, a compliance calendar, delegation-of-authority, document lifecycle, in-meeting mode, and regulator-ready search & exports.

## Epics (39 tasks, API-first)

| Epic | Theme | Tasks | Regulated |
|---|---|---|---|
| **G** | Statutory registers & directors' interests | P2-01…05 | CAMA |
| **H** | Recusal & voting | P2-06…09 | access control |
| **I** | Minute book & record integrity | P2-10…13 | CAMA / NDPA |
| **J** | Committees | P2-14…17 | — |
| **K** | Compliance & statutory calendar | P2-18…20 | CAMA / CBN |
| **L** | Delegation of authority & thresholds | P2-21…22 | CAMA |
| **M** | Document lifecycle (retention/offline/annotations) | P2-23…26 | NDPA |
| **N** | Meetings enhancements (in-meeting mode, virtual, group views) | P2-27…30 | — |
| **O** | Actions & notifications enhancements | P2-31…34 | — |
| **P** | Global search & regulator exports | P2-35…37 | permission-scoped |
| **Q** | Platform NFRs (backup/DR, a11y, low-bandwidth) | P2-38…39 | — |

## Checkpoints (built + tested, then `needs-review` — human merge gate)

P2-01 registers · P2-03 interests register · P2-06 item-level recusal · P2-08 recusal-in-voting · P2-10 minute book · P2-12 record integrity · P2-21 DoA/thresholds · P2-23 retention/legal-hold/purge · P2-35 permission-scoped search.

## Definition of done (per task)

Backend: models + migration + services + scoped/audited DRF endpoints + pytest green. Frontend: Northstar screen(s) + Vitest green + build-gated redeploy. Regulated tasks emit audit events and enforce entity-scope + least-privilege. Order: lowest-id whose deps are `done`.
