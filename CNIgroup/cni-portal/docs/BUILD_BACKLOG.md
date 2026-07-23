# Phase-1 Build Backlog — CNI Group Governance Portal

**Status:** Ready for the build-loop
**Prepared:** 2026-07-17
**Sources:** [PRD](../../PRD_Group_Governance_Portal.md) · [DECISIONS](../../DECISIONS.md) · [Design system](../../design-system/) · machine-readable mirror: [`backlog.yaml`](backlog.yaml)

This is the ordered work-list the build-loop consumes. It covers **Phase 1** (the MVP spine, security-complete), adjusted for **D-B1 = group tree immediately** (multi-entity + entity switcher are in Phase 1, not Phase 2).

---

## How the loop uses this backlog

For each iteration:
1. Pick the **lowest-numbered task whose dependencies are all `done`** and whose status is `todo`.
2. Implement it (backend + frontend as noted).
3. Run its **Definition of Done** — the listed automated tests must be **green**. Also run the full suite to catch regressions.
4. If green **and** the task is **not** a 🔒 checkpoint → mark `done`, advance.
5. If it **is** a 🔒 checkpoint → mark `needs-review` and **stop for a human**. Checkpoints are the security/permissions/audit/AI tasks where wrong-but-plausible is dangerous (DECISIONS D-D2). The loop never self-approves them.
6. The loop never performs irreversible/external actions (real deploys, real notifications, live e-sign, data deletion) — those are human-gated (D-D4).

**Legend:** 🔒 = human-review checkpoint · `[refs]` = PRD requirement IDs the task satisfies · **DoD** = automated tests that define "done".

**Cross-cutting rules** (apply to *every* task that mutates or reads data, enforced by tests in the relevant task):
- Every state change writes an append-only `AuditEvent` (depends T-A2).
- Every list/detail endpoint is permission-scoped; nothing is globally readable (depends T-B3, PRD P2).
- No PII in URLs/query strings; email notifications carry links only, never content (PRD P5).

---

## Dependency-ordered index

| # | Task | refs | depends on | 🔒 |
|---|---|---|---|---|
| T-A1 | Custom User model (email login) | FR-ADM-2 | T-000 (scaffold ✅) | 🔒 |
| T-A2 | Audit log core (append-only, hash-chained) | NFR-AUD-1 | T-A1 | 🔒 |
| T-A3 | MFA (TOTP) + session policy | NFR-SEC-1 | T-A1 | 🔒 |
| T-A4 | SSO (OIDC) — additive | NFR-SEC-1 | T-A3 | 🔒 |
| T-A5 | Secrets, encryption & residency config | NFR-SEC-2, NFR-SEC-3 | T-000 | 🔒 |
| T-B1 | Entity model + hierarchy + profile | FR-ENT-1, DM-1 | T-A1 | |
| T-B2 | RoleAssignment (scoped roles) | FR-RBAC-1 | T-B1 | 🔒 |
| T-B3 | Permission-resolution layer | FR-RBAC-1, P2 | T-B2, T-A2 | 🔒 |
| T-B4 | Break-glass access | FR-RBAC-3 | T-B3, T-A2 | 🔒 |
| T-B5 | Admin ≠ reader separation | NFR-SEC-4 | T-B3 | 🔒 |
| T-B6 | Entity CRUD API (scoped) | FR-ENT-1 | T-B3 | |
| T-B7 | Shell + entity switcher + group/entity views | FR-ENT-2 | T-B6, T-A3 | |
| T-B8 | User lifecycle (onboard/offboard, keep history) | FR-ADM-2, P6 | T-B2, T-A2 | 🔒 |
| T-C1 | Meeting model + scheduling/calendar | FR-MTG-1 | T-B6 | |
| T-C2 | Notice + consent-to-short-notice | FR-MTG-2 | T-C1 | |
| T-C3 | Agenda builder | FR-MTG-3 | T-C1 | |
| T-C4 | Attendance + live quorum | FR-MTG-5 | T-C1 | |
| T-D1 | Document library + versioning | FR-DOC-1, FR-DOC-2 | T-B6 | |
| T-D2 | Watermark + download control + storage | FR-DOC-3, NFR-SEC-2 | T-D1 | 🔒 |
| T-D3 | Board pack compilation | FR-MTG-4 | T-C3, T-D1 | |
| T-E1 | Minute drafting (agenda-linked) | FR-MIN-1 | T-C3 | |
| T-E2 | Minutes approval workflow | FR-MIN-2 | T-E1 | |
| T-F1 | In-meeting resolutions + numbering | FR-RES-1 | T-C3 | |
| T-F2 | Circular resolutions + e-sign handoff | FR-RES-2 | T-F1, T-A2 | 🔒 |
| T-F3 | Certified True Copy generation | FR-RES-4 | T-F1 | |
| T-G1 | Action capture | FR-ACT-1 | T-C3 | |
| T-G2 | Notifications (multi-channel) | FR-NOT-1, P5 | T-C1 | |
| T-G3 | Role dashboards | FR-RPT-2 | T-B7, T-C1, T-G1 | |
| T-G4 | Portal/entity settings | FR-ADM-1 | T-B6 | |

29 Phase-1 tasks (plus T-000 scaffold, done). 12 checkpoints (all in the security/permissions/identity/e-sign/content-leak spine — as intended).

---

## Epic A — Security & identity foundation

### T-A1 — Custom User model (email login)  [FR-ADM-2] 🔒
**Depends:** T-000 · **Build:** Custom `User` (email as username, name, is_active) + custom manager; swap `AUTH_USER_MODEL`. *Requires resetting the dev DB* (no real data yet) so the custom user precedes all FK references — do this before any other model.
**DoD:**
- `test_user_email_is_identifier` — Given a user created with email, When authenticating, Then email is the identifier and duplicate emails are rejected.
- `test_user_model_is_swapped` — `get_user_model()` resolves to the custom model; migrations reference it.
**Checkpoint:** foundational identity — human confirms the model before everything builds on it.

### T-A2 — Audit log core (append-only, hash-chained)  [NFR-AUD-1] 🔒
**Depends:** T-A1 · **Build:** `AuditEvent` (actor, action, target GFK, timestamp, ip/device, metadata, `prev_hash`, `hash`); a record service; block updates/deletes at the model level; export/filter API.
**DoD:**
- `test_event_is_append_only` — Given an AuditEvent, When update or delete is attempted, Then it raises / is refused.
- `test_hash_chain_detects_tampering` — Given a chain, When any row's content is altered, Then chain verification fails.
- `test_event_records_actor_action_target` — every event carries actor, action, target, timestamp.
**Checkpoint:** the integrity backbone; human review of the chaining scheme.

### T-A3 — MFA (TOTP) + session policy  [NFR-SEC-1] 🔒
**Depends:** T-A1 · **Build:** enforce TOTP enrolment + verification (django-otp), session timeout, concurrent-session control.
**DoD:**
- `test_login_requires_totp` — Given a user with MFA, When password-only, Then access to protected endpoints is denied until TOTP verified.
- `test_session_times_out` — inactivity beyond the configured window invalidates the session.
- `test_mfa_events_audited` — enrolment and verification write AuditEvents.
**Checkpoint:** authentication — human review.

### T-A4 — SSO (OIDC) additive  [NFR-SEC-1] 🔒
**Depends:** T-A3 · **Build:** OIDC login (Google / Microsoft Entra) that maps to existing users; MFA still enforced unless IdP asserts equivalent.
**DoD:**
- `test_oidc_maps_to_existing_user` — Given an allow-listed IdP identity, When logging in, Then it binds to the matching user; unknown identities are rejected.
**Checkpoint:** auth path — human review.

### T-A5 — Secrets, encryption & residency config  [NFR-SEC-2, NFR-SEC-3] 🔒
**Depends:** T-000 · **Build:** all secrets from env; TLS assumed at edge; per-document encryption hook for "crown jewels"; a `DATA_RESIDENCY` config flag that routes storage; assert no PII in query strings (lint/test).
**DoD:**
- `test_no_secrets_in_repo` — settings read from env; no hard-coded secret.
- `test_residency_flag_routes_storage` — Given a residency setting, Then storage backend selection honors it.
**Checkpoint:** encryption/residency — human + Legal (ties to D-B3).

---

## Epic B — Entities & tenancy (the group spine)

### T-B1 — Entity model + hierarchy + profile  [FR-ENT-1, DM-1]
**Depends:** T-A1 · **Build:** `Entity` with `parent` (self-FK tree), statutory profile fields (legal name, CAC RC, incorporation date, registered address, share capital, FY-end, cosec, auditors, regulators), "incomplete" flag when required fields missing.
**DoD:**
- `test_entity_tree` — Given an entity with a parent, Then it appears under that parent; cycles are rejected.
- `test_incomplete_flag` — missing statutory fields → entity flagged incomplete.

### T-B2 — RoleAssignment (scoped roles)  [FR-RBAC-1] 🔒
**Depends:** T-B1 · **Build:** `RoleAssignment` (person × role × scope[entity|committee|meeting]); role enum from PRD §3.1; one identity → many scoped assignments.
**DoD:**
- `test_role_scoped_to_entity` — Given NED on Entity A, Then no access to Entity B.
- `test_role_change_audited` — assignment changes write AuditEvents (actor, subject, scope).
**Checkpoint:** permissions model — human review.

### T-B3 — Permission-resolution layer  [FR-RBAC-1, P2] 🔒
**Depends:** T-B2, T-A2 · **Build:** resolution service across Entity→Committee→Meeting→Item; DRF permission classes; group-level vs entity-scoped roles both resolve (needed by D-B1); default-deny.
**DoD:**
- `test_no_cross_entity_leak` — a user cannot read another entity's objects via any endpoint.
- `test_group_role_sees_scoped_consolidation` — a group-level role sees only entities in its remit.
- `test_default_deny` — an endpoint with no explicit grant denies.
**Checkpoint:** the core of least-privilege — human review.

### T-B4 — Break-glass access  [FR-RBAC-3] 🔒
**Depends:** T-B3, T-A2 · **Build:** admin content access requires stated reason, is time-boxed, notifies the Company Secretary, logged high-severity.
**DoD:**
- `test_admin_denied_by_default` — admin without content role can't open board papers.
- `test_break_glass_requires_reason_and_audits` — invoking requires reason, expires, emits high-sev AuditEvent + cosec notification.
**Checkpoint:** privileged access — human review.

### T-B5 — Admin ≠ reader separation  [NFR-SEC-4] 🔒
**Depends:** T-B3 · **Build:** platform-admin role cannot silently read content; any content read by admin routes through break-glass.
**DoD:**
- `test_platform_admin_cannot_read_content_silently` — admin content read without break-glass is denied and/or logged.
**Checkpoint:** human review.

### T-B6 — Entity CRUD API (scoped)  [FR-ENT-1]
**Depends:** T-B3 · **Build:** DRF viewsets/serializers for entities, permission-scoped, audited; Django admin registration.
**DoD:**
- `test_entity_crud_scoped` — list/detail/create/update honor permissions and write audit events.

### T-B7 — Shell + entity switcher + group/entity views  [FR-ENT-2]
**Depends:** T-B6, T-A3 · **Build:** wire the Northstar Workspace Shell to real nav; entity switcher; group dashboard vs entity dashboard depending on the viewer's roles.
**DoD:**
- `test_switcher_lists_only_permitted_entities` (frontend + api).
- `e2e_group_role_sees_group_view` / `e2e_entity_role_sees_only_their_entity` (Playwright).

### T-B8 — User lifecycle  [FR-ADM-2, P6] 🔒
**Depends:** T-B2, T-A2 · **Build:** invite → onboard (scoped provisioning) → offboard (revoke access, **preserve** history & attributed actions); bulk import.
**DoD:**
- `test_offboard_revokes_but_preserves_history` — Given offboarding, Then access is revoked and prior AuditEvents/attributions remain intact.
**Checkpoint:** identity lifecycle — human review.

---

## Epic C — Meetings

### T-C1 — Meeting model + scheduling/calendar  [FR-MTG-1]
**Depends:** T-B6 · **Build:** `Meeting` (entity, type, datetime, tz, location/virtual), recurring series, availability polling.
**DoD:**
- `test_recurring_series_generates_meetings`; `test_meeting_scoped_to_entity`; `test_timezone_per_invitee`.

### T-C2 — Notice + consent-to-short-notice  [FR-MTG-2]
**Depends:** T-C1 · **Build:** configurable notice period per meeting type (seed CAMA defaults, cosec-confirmable — D-B5); short-notice warning + recorded consent; proof-of-service to audit.
**DoD:**
- `test_short_notice_requires_consent`; `test_notice_dispatch_proof_audited`.

### T-C3 — Agenda builder  [FR-MTG-3]
**Depends:** T-C1 · **Build:** `AgendaItem` (title, type Approval/Discussion/Noting, owner, time, linked papers), drag-reorder, auto-numbering + ToC, templates.
**DoD:**
- `test_reorder_renumbers_and_updates_toc`; `test_item_types_persist`.

### T-C4 — Attendance + live quorum  [FR-MTG-5]
**Depends:** T-C1 · **Build:** check-in (physical/virtual/proxy), live quorum indicator, apologies, per-director attendance stats.
**DoD:**
- `test_quorum_met_indicator`; `test_apologies_recorded`; `test_attendance_stats_persist`.

---

## Epic D — Documents & packs

### T-D1 — Document library + versioning  [FR-DOC-1, FR-DOC-2]
**Depends:** T-B6 · **Build:** `Document` + `Version` (content hash), taxonomy (entity→committee/meeting/topic), permission-inherited, full-text search (OCR later).
**DoD:**
- `test_new_version_retains_prior_and_hashes`; `test_search_is_permission_scoped`.

### T-D2 — Watermark + download control + storage  [FR-DOC-3, NFR-SEC-2] 🔒
**Depends:** T-D1 · **Build:** view-only vs downloadable per doc; per-viewer watermark (name/email/timestamp) on rendered/downloaded pages; S3-compatible encrypted storage, signed short-lived URLs.
**DoD:**
- `test_view_only_blocks_download`; `test_watermark_contains_viewer_identity`; `test_urls_are_signed_and_expire`.
**Checkpoint:** confidential-content leak surface — human review.

### T-D3 — Board pack compilation  [FR-MTG-4]
**Depends:** T-C3, T-D1 · **Build:** assemble agenda papers into paginated pack, cover + auto ToC (item→page), versioned, republish notice, late/supplementary marking.
**DoD:**
- `test_pack_toc_maps_items_to_pages`; `test_republish_increments_version_and_notifies`; `test_late_paper_flagged`.

---

## Epic E — Minutes

### T-E1 — Minute drafting (agenda-linked)  [FR-MIN-1]
**Depends:** T-C3 · **Build:** minute block per agenda item, attendees auto-populated, inline "create resolution/action".
**DoD:**
- `test_minutes_seed_from_agenda_and_attendees`; `test_inline_action_and_resolution_links`.

### T-E2 — Minutes approval workflow  [FR-MIN-2]
**Depends:** T-E1 · **Build:** states Draft→Chairman review→Circulated→Adopted→Signed, each logged; comments tracked and dispositioned before adoption.
**DoD:**
- `test_state_transitions_logged`; `test_comments_block_adoption_until_dispositioned`.

---

## Epic F — Resolutions

### T-F1 — In-meeting resolutions + numbering  [FR-RES-1]
**Depends:** T-C3 · **Build:** resolution text, mover/seconder, votes for/against/abstain/recused, outcome; auto-number per entity scheme (seed `‹ENTITY›/‹BODY›/‹YEAR›/‹SEQ›`, cosec-confirmable — D-B6).
**DoD:**
- `test_resolution_records_votes_and_outcome`; `test_auto_numbering_sequences_per_entity`.

### T-F2 — Circular resolutions + e-sign handoff  [FR-RES-2] 🔒
**Depends:** T-F1, T-A2 · **Build:** draft→circulate→per-director e-sign (DocuSign integration behind an interface; stubbed until vendor picked, D-B4)→effective on threshold, with reminders + expiry/lapse.
**DoD:**
- `test_effective_on_threshold`; `test_expiry_lapses`; `test_signature_events_audited`.
**Checkpoint:** signing/effectiveness of the record + external integration — human review; live e-sign calls stay human-gated (D-D4).

### T-F3 — Certified True Copy generation  [FR-RES-4]
**Depends:** T-F1 · **Build:** CTC of a passed/effective resolution — entity-branded, certification wording + cosec signature block, logged as issued.
**DoD:**
- `test_ctc_only_for_passed_resolution`; `test_ctc_logged_as_issued`.

---

## Epic G — Actions, notifications, dashboards, settings

### T-G1 — Action capture  [FR-ACT-1]
**Depends:** T-C3 · **Build:** action (owner incl. non-members, due date, source-item link) captured in-meeting.
**DoD:** `test_action_has_owner_due_and_source_link`.

### T-G2 — Notifications (multi-channel)  [FR-NOT-1, P5]
**Depends:** T-C1 · **Build:** email/SMS/push/in-portal with per-event preferences; **email contains only a link into the Portal, never content**.
**DoD:**
- `test_email_contains_link_not_content`; `test_event_preferences_respected`.

### T-G3 — Role dashboards  [FR-RPT-2]
**Depends:** T-B7, T-C1, T-G1 · **Build:** chairman (attendance/overdue/upcoming), cosec (compliance/pack status/signature queue), director (my meetings/actions/awaiting-signature).
**DoD:** `e2e_chairman_dashboard`, `e2e_director_dashboard` (Playwright, scoped).

### T-G4 — Portal/entity settings  [FR-ADM-1]
**Depends:** T-B6 · **Build:** per-entity branding, agenda/minutes/pack templates, resolution numbering scheme, retention & notification policies.
**DoD:** `test_entity_settings_persist_and_scope`.

---

## Out of Phase 1 (backlog for later phases — do NOT loop yet)
Statutory registers (FR-ENT-3), intercompany (FR-ENT-4), in-meeting mode (FR-MTG-7), virtual integration (FR-MTG-6), annotations (FR-DOC-4), retention/purge (FR-DOC-5), offline packs (FR-DOC-6), minute book immutability (FR-MIN-3), matters-arising (FR-MIN-4), thresholds/DoA (FR-RES-5), voting modes (FR-VOTE-*), conflicts/interests (FR-CONF-*), committees (FR-COM-*), compliance calendar (FR-CMP-*), evaluations (FR-EVAL-*), search (FR-RPT-1), exports (FR-RPT-3), **all AI (FR-AI-*, NFR-AI-* — Phase 3, guardrails ship with the first AI feature)**, API/webhooks (FR-ADM-3), sandbox (FR-ADM-4).

---

*The loop starts at T-A1. First three tasks (T-A1/A2/A3) are checkpoints, so expect a human-review pause early — by design: the identity/audit/auth spine is reviewed before the breadth is built on top of it.*
