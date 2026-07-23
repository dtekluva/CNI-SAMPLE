# Completion Backlog — Backend API + Frontend

**Status:** ✅ Complete — all tasks done (BE-1…BE-12, FE-1…FE-17). Backend 108 tests, frontend 32 tests, all green; live preview redeployed.
**Prepared:** 2026-07-17
**Sources:** [PRD](reference/PRD_Group_Governance_Portal.md) · [DECISIONS](reference/DECISIONS.md) · [Design system](reference/design-system/) · [Phase-1 backlog](BUILD_BACKLOG.md). Machine-readable driver: [`completion_backlog.yaml`](completion_backlog.yaml).

Phase 1 built the **domain models, services, and tests** for the whole platform, but two things are outstanding:
1. **Backend API layer** — most domains (meetings, documents, minutes, resolutions, actions, notifications, audit) have services + tests but **no REST endpoints**. The frontend can't consume them yet.
2. **Frontend** — only a shell + 2 components exist; the real governance screens aren't built.

This backlog finishes both, API-first (screens depend on endpoints), plus small backend follow-ups (PDF rendering, mailer tie-up).

## Loop protocol (same as before)
Pick the lowest-id task whose deps are `done`; build it; run its DoD (**pytest** for backend APIs, **Vitest + build** for frontend, live-deploy where it helps); green → `done`, checkpoint → `needs-review`. Never commit secrets (`.env` stays gitignored). Frontend verified in-browser against the live URL where feasible; otherwise component tests + build are the gate.

**Legend:** 🔒 checkpoint (new content-exposure surface) · DoD = tests that define done.

---

## Part 1 — Backend API layer (API-first; frontend depends on it)

### BE-1 — Meetings API  [FR-MTG-1/2/5]
Scoped viewset (list/detail/create), quorum-status action, notice-dispatch + short-notice-consent actions. **DoD:** `test_meetings_api_scoped`, `test_quorum_action`, `test_notice_action`.

### BE-2 — Agenda API  [FR-MTG-3]
Agenda items under a meeting: list/create/reorder + ToC endpoint. **DoD:** `test_agenda_crud_and_reorder`, `test_toc_endpoint`.

### BE-3 — Documents API 🔒  [FR-DOC-1/2/3]
Scoped library list/detail, versions, **download-request** (view-only blocked, signed URL), search. **DoD:** `test_documents_scoped`, `test_download_request_blocks_view_only`, `test_search_scoped`.

### BE-4 — Board pack API  [FR-MTG-4]
Compile pack action + retrieve ToC/versions. **DoD:** `test_compile_pack_api`, `test_pack_toc_api`.

### BE-5 — Minutes API  [FR-MIN-1/2]
Seed/retrieve minutes, blocks, inline decisions, workflow transitions, comments. **DoD:** `test_minutes_seed_api`, `test_minutes_transition_api`, `test_comment_blocks_adoption_api`.

### BE-6 — Resolutions API 🔒  [FR-RES-1/2/4]
List/detail/create scoped, vote, conclude, circulate, **sign**, generate CTC. **DoD:** `test_resolutions_scoped`, `test_vote_and_conclude_api`, `test_sign_and_ctc_api`.

### BE-7 — Actions API  [FR-ACT-1]
Scoped list (mine/overdue), create, complete. **DoD:** `test_actions_scoped`, `test_complete_action_api`.

### BE-8 — Notifications API  [FR-NOT-1]
My notifications (list/mark-read), preferences get/set. **DoD:** `test_my_notifications_api`, `test_preferences_api`.

### BE-9 — Audit log API 🔒  [NFR-AUD-1]
Scoped, read-only, filterable audit export. **DoD:** `test_audit_api_scoped_readonly`, `test_audit_filter`.

### BE-10 — PDF render: board pack  [FR-MTG-4]
Render the compiled pack to a real PDF (cover + ToC + papers placeholder + per-viewer watermark stamp). **DoD:** `test_pack_pdf_bytes_and_watermark`.

### BE-11 — PDF render: CTC  [FR-RES-4]
Render CTC to a branded PDF. **DoD:** `test_ctc_pdf_bytes`.

### BE-12 — Mailer tie-up  [FR-NOT-1]
Commit the (secret-free) mailer + delivery wiring; management command to send a test; delivery stays env-gated. **DoD:** `test_mailer_configured_flag`, `test_notify_calls_delivery_when_enabled` (mocked).

---

## Part 2 — Frontend (consumes the APIs above)

### FE-1 — Northstar React components  [Design Vol V]
Reusable Button, Badge, Field, Card, ApprovalCard, AIInsightPanel, Timeline, Shell — from the tokens/CSS. **DoD:** Vitest render tests per component; build green.

### FE-2 — API client + auth context  [NFR-SEC-1]
fetch wrapper (JSON, CSRF token, credentials), `useAuth` (login/logout/me), MFA state. **DoD:** `apiClient.test`, `auth-context.test` (mocked fetch).

### FE-3 — Router + protected routes + AppShell  [FR-ENT-2]
Routing, redirect-to-login when unauthenticated, workspace shell (nav + entity switcher). **DoD:** `protected-route.test`, `shell.test`.

### FE-4 — Login screen  [NFR-SEC-1]
Email/password → session. **DoD:** `login.test` (submit → calls API → routes on success/failure).

### FE-5 — MFA screen  [NFR-SEC-1]
TOTP enrol (QR/secret) + verify. **DoD:** `mfa.test`.

### FE-6 — Dashboard screen  [FR-RPT-2]
Real scoped summary + quick actions. **DoD:** `dashboard-screen.test`.

### FE-7 — Entities screen  [FR-ENT-1/2]
Group tree / list + entity profile. **DoD:** `entities-screen.test`.

### FE-8 — Meetings screen  [FR-MTG-1]
List + calendar; create meeting. **DoD:** `meetings-screen.test`.

### FE-9 — Board Meeting workspace  [FR-MTG-3/5]
Agenda (typed items), live quorum, attendance, papers, in-context actions. **DoD:** `meeting-workspace.test`.

### FE-10 — Agenda builder  [FR-MTG-3]
Add/reorder items, types, owners, ToC. **DoD:** `agenda-builder.test`.

### FE-11 — Documents + pack reader  [FR-DOC-1/3, FR-MTG-4]
Library, view-only vs download, watermark notice, pack ToC reader. **DoD:** `documents-screen.test`.

### FE-12 — Minutes editor  [FR-MIN-1/2]
Item-by-item minutes + workflow state + comments. **DoD:** `minutes-editor.test`.

### FE-13 — Resolutions screen  [FR-RES-1/2/4]
List/detail, ApprovalCard voting, circular signing, CTC issue. **DoD:** `resolutions-screen.test`.

### FE-14 — Actions screen  [FR-ACT-1]
My actions + overdue, complete with evidence. **DoD:** `actions-screen.test`.

### FE-15 — Notifications + preferences  [FR-NOT-1]
In-portal inbox, read receipts, channel preferences. **DoD:** `notifications-screen.test`.

### FE-16 — Audit log viewer  [NFR-AUD-1]
Scoped, filterable audit timeline. **DoD:** `audit-viewer.test`.

### FE-17 — Settings screen  [FR-ADM-1]
Per-entity branding/numbering/retention/notification policy. **DoD:** `settings-screen.test`.

---

## Sequencing
Backend API (BE-1…BE-12) first — the frontend consumes it. FE-1…FE-3 (components, client, shell, auth) are the frontend foundation; FE-4…FE-17 are screens, each wired to its API. Tie-up at the end: full-suite green, redeploy the live preview, update docs/memory.

*29 tasks (12 backend API/follow-up + 17 frontend). Checkpoints: BE-3, BE-6, BE-9 (content-exposure surfaces over HTTP).*
