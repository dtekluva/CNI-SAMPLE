# Product Requirements Document — Group Governance Portal

**Product:** Liberty Group Governance Portal ("the Portal")
**Working codename:** Directors' Portal
**Document status:** Draft v0.1 — for design & UX discussion
**Prepared:** 2026-07-17
**Owner:** CTO, Liberty Pay
**Audience:** Product, Design, Engineering, Company Secretariat, Board

---

## 0. How to read this document

This PRD is deliberately **exhaustive**. It defines *what* the Portal must do and *why*, not *how* it looks — design language, visual system, and detailed UX come in the next phase and will reference the requirement IDs here.

**Conventions**

- Every requirement has a stable ID: `FR-<domain>-<n>` (functional), `NFR-<domain>-<n>` (non-functional), `DM-<n>` (data model).
- User stories use the form: *As a `<role>`, I want `<capability>`, so that `<outcome>`.*
- Acceptance criteria use **Given / When / Then**. They are testable; if a criterion can't be tested, it's a goal, not a criterion.
- **MoSCoW priority** per capability: **M**ust / **S**hould / **C**ould / **W**on't-yet.
- **Phase** tags map to the rollout plan in §21.

**Regulatory frame.** Liberty is a Nigerian group with a CBN-regulated payments entity. The Portal must respect: **CAMA 2020** (Companies and Allied Matters Act — statutory registers, notice periods, resolutions, filings), **CBN corporate governance guidelines** (board composition, director training, tenure, committees), **NDPA 2023** (Nigeria Data Protection Act — data residency, consent, subject rights), and **NGX/SEC codes** where a group entity is listed or intends to be. Requirements traceable to a regulation are tagged `[REG:<source>]`.

---

## 1. Problem statement, vision, goals

### 1.1 Problem
Board and committee governance across the Liberty group is currently run over email, shared drives, and WhatsApp. This creates: uncontrolled distribution of confidential board papers; no audit trail of who saw what; version chaos in packs and minutes; manual, error-prone resolution and minute-book keeping; no consolidated view across group entities; and weak, retrofit-resistant security on the group's most sensitive corpus.

### 1.2 Vision
A single, secure, multi-entity governance portal that is the system of record for every board and committee in the group — meetings, papers, minutes, resolutions, statutory registers, and compliance — with an immutable audit trail and security designed in from the first commit.

### 1.3 Goals (outcomes, not features)
- **G1** — Zero board papers distributed by email attachment within 2 quarters of rollout.
- **G2** — Every meeting, minute, and resolution for every group entity is discoverable in one place, permission-scoped.
- **G3** — Company Secretary produces a regulator-ready minute book, resolution register, and attendance register per entity in one click.
- **G4** — Full, exportable, tamper-evident audit trail of access to confidential content.
- **G5** — Group-level compliance status (CAC/CBN/tax) visible at a glance with owners and deadlines.
- **G6** — Directors read and act on packs from tablets/phones, including offline.

### 1.4 Non-goals (this product)
- Not a general DMS, HRIS, or intranet.
- Not accounting/ERP; it references financials as papers, it doesn't compute them.
- Not a public shareholder/investor-relations site (AGM support is in-scope; public IR is not).
- Not a replacement for the statutory CAC portal; it prepares and tracks filings, it doesn't file to CAC directly (until an integration exists).

### 1.5 Success metrics
- % of meetings run fully in-portal (target ≥ 90% by end of Phase 2).
- % packs distributed with zero email attachments (target 100%).
- Median time to compile & publish a board pack (baseline vs target −60%).
- Median time to produce a Certified True Copy of a resolution (target < 5 min).
- Director weekly active usage during meeting weeks (target ≥ 85%).
- Audit-log completeness (target 100% of content access events logged).

### 1.6 Personas
| Persona | Role in system | Primary needs |
|---|---|---|
| **Adaeze — Company Secretary (Group)** | Cosec / power admin | Compile packs, run meetings, keep minute book & registers, track compliance across all entities |
| **Chief Bala — Group Chairman** | Chairman | Cross-entity oversight, attendance & action visibility, approve minutes, read receipts on packs |
| **Mrs. Okonkwo — Non-Executive/Independent Director** | Director | Read packs (often offline on iPad), declare conflicts, vote, sign resolutions, track her actions |
| **Emeka — Executive Director / CFO** | Director + presenter | Present agenda items, upload papers, respond to actions |
| **Tunde — Subsidiary MD** | Entity admin (scoped) | Run his subsidiary's board, feed reports up to holdco |
| **External Auditor** | Time-boxed read-only | Access specific packs/minutes for a defined window |
| **Ngozi — Portal Administrator (IT)** | Platform admin | User lifecycle, security config, integrations, backups — *without* silent access to board content |

---

## 2. System-wide principles & constraints

- **P1 — Security is not a feature, it's the substrate.** MFA, encryption, and audit logging exist from day one, not phase 3. `[REG:NDPA]`
- **P2 — Least privilege, scoped per entity.** No global "see everything" except through logged, break-glass access.
- **P3 — Multi-entity in the data model from day one.** The UI may ship single-entity first; the schema must not.
- **P4 — Immutability of the record.** Signed minutes, resolutions, and audit logs are append-only and tamper-evident.
- **P5 — No email attachments, ever.** Email carries links into the Portal, never confidential content.
- **P6 — The record survives the person.** Offboarding a director revokes access but preserves their historical audit trail and attributed actions.
- **P7 — Admin ≠ reader.** Platform administration is separated from content access; admin reads of content are themselves privileged, logged events.
- **P8 — Offline-first reading.** Packs must be readable without connectivity, with encrypted local storage and remote wipe.
- **P9 — Nigerian reality.** Low-bandwidth mode, CTC generation, circular resolutions, and CAC/CBN calendars are first-class, not afterthoughts.
- **P10 — AI assists; people decide.** AI is *assistive, never autonomous*. It drafts, summarizes, surfaces, and explains — it never signs, votes, approves, publishes, files, alters, or deletes anything on the record. Every AI output lands in front of a human who decides. AI is always identifiable, always explainable, always permission-scoped, and always off until switched on. This is a bounded assistant, **not** an agent that acts for the board. `[REG:NDPA]`

---

## 3. Roles & permission model

### 3.1 Roles
`Super Administrator`, `Company Secretary`, `Chairman`, `Executive Director`, `Non-Executive Director`, `Independent Director`, `Committee Member`, `Presenter/Invitee`, `Auditor (read-only, time-boxed)`, `Legal Counsel`, `Portal Administrator (IT)`.

Roles are **assigned per entity and per committee**, not globally. A person is one identity with many scoped role-assignments.

### 3.2 Permission dimensions
Permissions resolve across: **Entity → Committee → Meeting → Agenda item → Document**. Access can be granted or revoked at any level, and item-level revocation (recusal) overrides inherited grants.

### FR-RBAC-1 — Scoped role assignment `[M][Phase 1]`
**Story:** As a Company Secretary, I want to assign a person a role on a specific entity/committee, so that their access is limited to exactly what their appointment covers.
**AC:**
- Given a person exists, When I assign them "Non-Executive Director" on Entity A, Then they can access Entity A board content and cannot see Entity B.
- Given a director sits on two entities, When their role differs per entity, Then permissions resolve independently per entity with no leakage.
- Given any role assignment change, Then it is written to the audit log with actor, subject, scope, and timestamp.

### FR-RBAC-2 — Item-level recusal overrides inheritance `[M][Phase 2]`
**Story:** As a Company Secretary, I want a conflicted director blocked from a specific agenda item's papers and vote, so that conflicts are enforced, not just noted.
**AC:**
- Given a director is marked conflicted on item 4, When the pack is published, Then item 4's papers are not visible/downloadable to them and item 4 does not appear in their voting list.
- Given the recusal, Then the minutes and audit log record the exclusion automatically.

### FR-RBAC-3 — Break-glass admin access `[M][Phase 1]`
**Story:** As a Portal Administrator, I want a break-glass path to content only when operationally required, so that admins can support the system without silently reading board papers.
**AC:**
- Given an admin has no content role on an entity, When they attempt to open a board paper, Then access is denied by default.
- Given break-glass is invoked, Then it requires a stated reason, is time-boxed, notifies the Company Secretary, and is logged as a high-severity audit event.

### FR-RBAC-4 — Delegation & alternates `[S][Phase 3]`
**Story:** As a director, I want to appoint an alternate for a specific meeting, so that my seat is covered when I'm unavailable.
**AC:**
- Given I nominate an alternate for Meeting X, When the Cosec approves, Then the alternate gets scoped access to Meeting X only, expiring when the meeting closes.

---

## 4. Group & entity structure

### DM-1 — Entity hierarchy
Entities form a tree: Holding Company → Subsidiaries → Sub-subsidiaries. Each entity owns its own boards, committees, calendar, documents, registers, and role-assignments.

### FR-ENT-1 — Entity profile `[M][Phase 1]` `[REG:CAMA]`
**Story:** As a Company Secretary, I want each entity to hold its statutory particulars, so that the Portal is the source of truth for corporate data.
**AC:**
- Given I create an entity, Then I can record: legal name, CAC RC number, incorporation date, registered address, share capital, financial year-end, company secretary, auditors, and regulators.
- Given an entity has a parent, When I set the parent, Then it appears in the group tree under that parent.
- Given required statutory fields are missing, Then the entity is flagged "incomplete" on the compliance dashboard.

### FR-ENT-2 — Group vs entity views `[M][Phase 2]`
**Story:** As a Group Chairman, I want a consolidated view across all entities I oversee, so that I can see group-wide governance without logging into each board.
**AC:**
- Given I hold a group-level role, When I open the group dashboard, Then I see consolidated calendar, resolutions register, and compliance status across entities I'm entitled to.
- Given a subsidiary director with no group role, When they log in, Then they see only their entity and never a group view.

### FR-ENT-3 — Statutory registers per entity `[M][Phase 2]` `[REG:CAMA]`
**Story:** As a Company Secretary, I want CAMA-mandated registers maintained per entity, so that we are statutorily compliant and audit-ready.
**AC:**
- Given an entity, Then I can maintain: Register of Directors, Register of Members/Shareholders, Register of Charges, and Register of Persons with Significant Control (beneficial ownership).
- Given any register entry changes, Then the change is versioned with effective date and logged.
- Given a regulator request, When I export a register, Then it produces a dated, entity-branded PDF/Excel.

### FR-ENT-4 — Intercompany governance `[S][Phase 3]`
**Story:** As a Company Secretary, I want subsidiary resolutions that require parent ratification to flow to the holdco, so that group approval chains are enforced.
**AC:**
- Given a subsidiary resolution is flagged "requires holdco ratification", When it passes at subsidiary level, Then a ratification item is created on the holdco's queue and the subsidiary resolution shows "pending parent ratification" until completed.

---

## 5. Meetings lifecycle

### FR-MTG-1 — Annual calendar & scheduling `[M][Phase 1]`
**Story:** As a Company Secretary, I want to plan a year of board and committee meetings, so that directors can reserve dates well ahead.
**AC:**
- Given an entity, When I create a meeting series, Then recurring meetings are generated with dates, times, timezone, and location/virtual details.
- Given a proposed date, When I open availability polling, Then invitees can indicate availability and I can see a heatmap before confirming.
- Given diaspora directors, Then each invitee sees times in their own timezone.

### FR-MTG-2 — Statutory notice & consent to short notice `[M][Phase 1]` `[REG:CAMA]`
**Story:** As a Company Secretary, I want the system to enforce minimum notice periods, so that meetings are validly convened.
**AC:**
- Given a meeting type with a statutory minimum notice, When I schedule inside that window, Then the system warns and requires recording "consent to short notice" from members before proceeding.
- Given a notice is dispatched, Then proof of service (recipient, channel, timestamp) is stored in the audit log.

### FR-MTG-3 — Agenda builder `[M][Phase 1]`
**Story:** As a Company Secretary, I want to build a structured agenda with item owners and linked papers, so that the meeting runs to a clear plan.
**AC:**
- Given a meeting, When I add agenda items, Then each item has: title, type (Approval/Discussion/Noting), owner/presenter, time allocation, and linked papers.
- Given I reorder items, Then numbering and the pack table of contents update automatically.
- Given standing agendas (e.g., Audit Committee), Then I can apply a template.

### FR-MTG-4 — Board pack compilation `[M][Phase 1]`
**Story:** As a Company Secretary, I want to assemble papers into one paginated pack, so that directors read a single, coherent document.
**AC:**
- Given agenda items with papers, When I compile the pack, Then it produces a paginated document with cover page and auto table of contents mapping items → pages.
- Given I republish after a change, Then affected directors are notified "pack updated" and the version increments; prior versions remain retrievable.
- Given a late paper, When I add it after publish, Then it is marked "late/supplementary" and flagged in the ToC.

### FR-MTG-5 — Attendance & quorum `[M][Phase 1]` `[REG:CAMA]`
**Story:** As a Chairman, I want live quorum status and an attendance register, so that the meeting is validly constituted and attendance is recorded.
**AC:**
- Given a meeting's quorum rule, When attendees check in (physical/virtual/proxy), Then a live indicator shows quorum met/not met.
- Given apologies, Then they are recorded and reflected in the attendance register.
- Given the meeting closes, Then attendance statistics are stored per director (feeding evaluations and annual-report disclosures).

### FR-MTG-6 — Virtual meeting integration `[S][Phase 2]`
**Story:** As a director, I want the join link on the meeting, so that I can attend virtually without hunting for details.
**AC:**
- Given a virtual meeting, Then Zoom/Teams/Meet link and dial-in fallback appear on the invite and meeting screen.
- Given a recording is captured, Then it is stored under the meeting with a retention rule applied.

### FR-MTG-7 — In-meeting mode `[S][Phase 2]`
**Story:** As a Chairman, I want a synchronized "follow the presenter" view, so that everyone is on the same page during discussion.
**AC:**
- Given in-meeting mode is active, When the presenter changes page, Then attendees in "follow" mode see the same page; they can break to browse and rejoin.
- Given a live agenda tracker, Then elapsed vs allocated time per item is visible.
- Given a motion is raised, Then mover/seconder/vote can be captured live and linked to the item.

### FR-MTG-8 — AGM/EGM support `[C][Phase 3]` `[REG:CAMA]`
**Story:** As a Company Secretary, I want shareholder-meeting support, so that AGMs/EGMs run with proxies and polls.
**AC:**
- Given an AGM, Then I can issue proxy forms, collect proxy appointments, and run poll voting with results captured.

---

## 6. Documents & board papers

### FR-DOC-1 — Entity document library `[M][Phase 1]`
**Story:** As a director, I want a permissioned library of my entity's documents, so that I can find papers by meeting, committee, or topic.
**AC:**
- Given the library, Then documents are organized by entity → committee/meeting/topic, and access inherits from that structure.
- Given full-text search, When I search, Then results are scoped to what I'm permitted to see (OCR'd scans included).

### FR-DOC-2 — Versioning & integrity `[M][Phase 1]`
**Story:** As a Company Secretary, I want versioned documents with integrity hashes, so that we always know the authoritative copy.
**AC:**
- Given a document is updated, Then a new version is stored, prior versions retained, and each version carries a content hash.

### FR-DOC-3 — Watermarking & download control `[M][Phase 1]`
**Story:** As a Company Secretary, I want per-document distribution controls, so that confidential papers can't leak untraced.
**AC:**
- Given a document, Then I can set it view-only (no download/print) or downloadable.
- Given any rendered/downloaded page, Then it is watermarked with the viewer's name, email, and timestamp.

### FR-DOC-4 — Annotations `[S][Phase 2]`
**Story:** As a director, I want private and shared annotations on papers, so that I can prepare and collaborate.
**AC:**
- Given a paper, When I annotate, Then I can keep notes private or share with named recipients.
- Given a pack is republished, Then my annotations re-map to the correct pages where content is unchanged, and are flagged where pages shifted. *(Known hard problem — see §19 risks.)*

### FR-DOC-5 — Retention, legal hold & secure purge `[S][Phase 2]` `[REG:NDPA]`
**Story:** As a Company Secretary, I want retention policies and legal holds, so that we keep what we must and destroy what we should.
**AC:**
- Given a retention policy, When a document reaches end-of-life and is not under legal hold, Then it is purged and a certificate of destruction is recorded.
- Given a "wipe pack after meeting" flag, When the meeting closes, Then local and server copies of that pack are revoked.

### FR-DOC-6 — Offline packs with remote wipe `[S][Phase 2]`
**Story:** As a director, I want packs available offline on my tablet, so that I can read without connectivity.
**AC:**
- Given I download a pack to the mobile app, Then it is stored encrypted locally and accessible offline.
- Given my access is revoked or the pack is wiped, When my device next connects (or via push), Then the local copy is remotely wiped.

---

## 7. Minutes

### FR-MIN-1 — Agenda-linked minute drafting `[M][Phase 1]`
**Story:** As a Company Secretary, I want to draft minutes item-by-item against the agenda, so that minutes are structured and complete.
**AC:**
- Given a meeting, When I open minutes, Then attendees auto-populate and each agenda item has a minute block.
- Given I capture a decision, Then I can flag it to create a linked resolution or action item inline.

### FR-MIN-2 — Minutes approval workflow `[M][Phase 1]`
**Story:** As a Chairman, I want a controlled draft→review→approve flow, so that minutes are properly adopted.
**AC:**
- Given a draft, Then it moves through states: Draft → Chairman review → Circulated for comment → Adopted → Signed, each state change logged.
- Given directors comment, Then comments are tracked and must be dispositioned before adoption.

### FR-MIN-3 — Immutable signed minutes & minute book `[M][Phase 2]` `[REG:CAMA]`
**Story:** As a Company Secretary, I want adopted minutes locked and compiled into a per-entity minute book, so that we hold a statutory record.
**AC:**
- Given minutes are signed, Then they are locked as an immutable PDF with e-signature and content hash; further edits require a formal correction at the next meeting.
- Given an entity, When I open the minute book, Then all adopted minutes are compiled chronologically and exportable.

### FR-MIN-4 — Matters arising auto-carry `[S][Phase 2]`
**Story:** As a Company Secretary, I want unresolved actions to flow into the next agenda, so that nothing is dropped.
**AC:**
- Given open actions from prior minutes, When I build the next agenda, Then a "matters arising" section is pre-populated with their status.

---

## 8. Resolutions & approvals

### FR-RES-1 — In-meeting resolutions `[M][Phase 1]` `[REG:CAMA]`
**Story:** As a Company Secretary, I want to record board resolutions with movers, votes, and outcomes, so that decisions are authoritatively captured.
**AC:**
- Given an agenda item for approval, When the vote concludes, Then I record: resolution text, mover, seconder, votes for/against/abstain/recused, and outcome.
- Given a passed resolution, Then it is auto-numbered per the entity's scheme (e.g., `LP/BD/2026/014`).

### FR-RES-2 — Written/circular resolutions `[M][Phase 1]` `[REG:CAMA]`
**Story:** As a Company Secretary, I want to circulate resolutions for signature between meetings, so that routine approvals don't wait for a meeting.
**AC:**
- Given a draft circular resolution, When I circulate it, Then each director receives it for e-signature with reminders and an expiry.
- Given the approval threshold is met, Then the resolution becomes effective and dated; if it expires first, it lapses with status recorded.

### FR-RES-3 — Resolution register & search `[M][Phase 2]`
**Story:** As a Company Secretary, I want a searchable resolution register per entity and consolidated for the group, so that past decisions are findable.
**AC:**
- Given resolutions exist, When I filter by topic/date/entity/type, Then matching resolutions are listed with links to source meeting/minutes.

### FR-RES-4 — Certified True Copy generation `[M][Phase 1]`
**Story:** As a Company Secretary, I want to generate a Certified True Copy of a resolution, so that I can serve banks and CAC quickly.
**AC:**
- Given a passed/effective resolution, When I generate a CTC, Then it produces a formatted, entity-branded document with certification wording and cosec signature block, logged as issued.
- Given a CTC is generated, Then median time from request to document is under 5 minutes (metric G/§1.5).

### FR-RES-5 — Thresholds, special resolutions & DoA `[S][Phase 2]` `[REG:CAMA]`
**Story:** As a Company Secretary, I want the system to enforce approval thresholds and a delegated-authority matrix, so that decisions are validly and correctly authorized.
**AC:**
- Given a special resolution, Then it requires the statutory ≥75% threshold to pass.
- Given a Delegation of Authority matrix (who approves what up to what limit), When a resolution/approval is raised, Then it is validated against the matrix and flagged if out of authority.

---

## 9. Voting & e-signatures

### FR-VOTE-1 — Multiple voting modes `[S][Phase 2]`
**Story:** As a Chairman, I want open, secret-ballot, and poll voting, so that each decision uses the appropriate method.
**AC:**
- Given a motion, When I choose a mode, Then votes are collected accordingly; secret ballots hide individual choices while recording the tally.

### FR-VOTE-2 — Recusal enforcement in voting `[M][Phase 2]`
**Story:** As a Company Secretary, I want conflicted directors excluded from a vote, so that outcomes are clean.
**AC:**
- Given a conflicted director on an item, When voting opens, Then they cannot vote on it and the minutes record the exclusion.

### FR-SIGN-1 — Integrated e-signature `[M][Phase 1]` `[REG:NDPA]`
**Story:** As a director, I want to e-sign minutes and resolutions in-portal, so that I don't print, sign, and scan.
**AC:**
- Given a document requiring my signature, When I sign, Then a signature certificate and document hash are stored, and the signed artifact is tamper-evident.
- Given signing, Then it works on mobile.

---

## 10. Directors' interests, conflicts & declarations

### FR-CONF-1 — Register of directors' interests `[M][Phase 2]` `[REG:CAMA]`
**Story:** As a director, I want to declare my other directorships, shareholdings, and related parties, so that my interests are on record.
**AC:**
- Given the register, When I add/update an interest, Then it is versioned with effective date and visible to the Cosec/Chairman.
- Given annual cycle, Then the system prompts me to review and re-attest my interests.

### FR-CONF-2 — Per-meeting conflict declaration `[M][Phase 2]`
**Story:** As a director, I want to declare conflicts against specific agenda items, so that recusal is enforced (links to FR-RBAC-2, FR-VOTE-2).
**AC:**
- Given a published agenda, When I declare a conflict on item N, Then I lose access to item N's papers and vote, and it's minuted.

### FR-CONF-3 — Related-party & gifts registers `[S][Phase 3]`
**Story:** As a Company Secretary, I want related-party transactions and a gifts/hospitality register, so that the Audit Committee has oversight.
**AC:**
- Given a related-party transaction is logged, Then it appears in the Audit Committee's feed with the parties and value.

### FR-CONF-4 — Fit-and-proper & compliance attestations `[S][Phase 3]` `[REG:CBN]`
**Story:** As a Company Secretary, I want directors to complete periodic fit-and-proper and compliance attestations, so that we meet regulator obligations.
**AC:**
- Given an attestation cycle, When it opens, Then directors are prompted, completion is tracked, and overdue attestations are escalated.

---

## 11. Committees

### FR-COM-1 — Committee setup & charters `[M][Phase 2]`
**Story:** As a Company Secretary, I want to define committees with terms of reference, so that each committee's mandate is documented.
**AC:**
- Given an entity, When I create a committee (Audit, Risk, Remuneration/Nomination, IT/Cyber, Credit, etc.), Then I attach its charter/ToR with a review date.
- Given a charter review date approaches, Then a reminder is raised.

### FR-COM-2 — Membership terms & rotation `[S][Phase 2]`
**Story:** As a Company Secretary, I want committee membership terms with expiry, so that rotation is planned.
**AC:**
- Given a membership term, When expiry approaches, Then an alert is raised for renewal or rotation.

### FR-COM-3 — Committee-to-board reporting `[S][Phase 2]`
**Story:** As a committee chair, I want to package committee recommendations up to the board, so that the board acts on our work.
**AC:**
- Given committee minutes/recommendations, When I promote them, Then they attach to the parent board's agenda as a reporting item.

### FR-COM-4 — Cross-entity (group) committees `[C][Phase 3]`
**Story:** As a Group Company Secretary, I want a group-level committee overseeing subsidiaries, so that group risk/audit is coordinated.
**AC:**
- Given a group committee, Then its members may draw from multiple entities and it can view scoped inputs from those entities.

---

## 12. Compliance & statutory calendar

### FR-CMP-1 — Compliance calendar per entity `[M][Phase 2]` `[REG:CAMA][REG:CBN]`
**Story:** As a Company Secretary, I want a calendar of statutory obligations per entity, so that nothing is filed late.
**AC:**
- Given an entity, Then I can record obligations (CAC annual returns, AGM deadline, financial statement filing, CBN/NDIC/tax returns, license renewals) with owner, due date, reminders, and escalation.
- Given a due date approaches, Then the owner is reminded on a cascade and the Cosec is notified on breach risk.

### FR-CMP-2 — Filing tracker & evidence `[M][Phase 2]`
**Story:** As a Company Secretary, I want to track filing status with evidence, so that we can prove compliance.
**AC:**
- Given an obligation, When I file, Then I set status (Due/Filed) and attach evidence; the consolidated dashboard shows RAG status per entity.

### FR-CMP-3 — Policy library & attestations `[S][Phase 3]`
**Story:** As a Company Secretary, I want a policy library with review cycles and director attestations, so that governance policies are current and acknowledged.
**AC:**
- Given a policy (board charter, code of conduct, whistleblowing, related-party), Then it has a review cycle, and directors are prompted to attest "read and accept" with completion tracked.

### FR-CMP-4 — Regulatory correspondence log `[C][Phase 3]`
**Story:** As a Company Secretary, I want to log regulator letters and response deadlines, so that we respond on time.
**AC:**
- Given inbound correspondence, When I log it, Then it has a deadline, owner, and status, and appears on the compliance dashboard.

---

## 13. Action items & matters arising

### FR-ACT-1 — Action capture & assignment `[M][Phase 1]`
**Story:** As a Company Secretary, I want to capture actions with owners and due dates during a meeting, so that decisions turn into work.
**AC:**
- Given an in-meeting action, When I create it, Then it has owner (including non-members like management), due date, and links to its source item.

### FR-ACT-2 — Reminders, escalation & evidence `[M][Phase 2]`
**Story:** As an action owner, I want reminders and a way to close actions with evidence, so that follow-through is tracked.
**AC:**
- Given an open action, When it nears/passes due, Then the owner is reminded and overdue actions escalate to Cosec/Chairman.
- Given completion, When I close it, Then I can attach evidence and the status is logged.

### FR-ACT-3 — Overdue-actions dashboard `[S][Phase 2]`
**Story:** As a Chairman, I want an overdue-actions view by entity and owner, so that I can chase in one place.
**AC:**
- Given open actions, Then a dashboard groups them by entity and owner with age.

---

## 14. Board evaluation & governance health

### FR-EVAL-1 — Board/committee/director evaluations `[C][Phase 3]` `[REG:CBN]`
**Story:** As a Chairman, I want annual evaluations, so that board effectiveness is measured and improved.
**AC:**
- Given an evaluation cycle, Then I can build questionnaires, collect anonymous responses, and view year-on-year benchmarking and a results pack.

### FR-EVAL-2 — Skills matrix & succession `[C][Phase 3]`
**Story:** As a Chairman, I want a board skills matrix and tenure/independence tracking, so that succession and nominations are informed.
**AC:**
- Given directors' skills and tenures, Then I can view competency gaps, term limits, retirement-by-rotation, and independence status (e.g., independence lost after defined tenure).

### FR-EVAL-3 — Training/CPD log `[C][Phase 3]` `[REG:CBN]`
**Story:** As a Company Secretary, I want a director training log, so that CBN training obligations are evidenced.
**AC:**
- Given training events, When recorded, Then per-director CPD is tracked and exportable.

---

## 15. Notifications & communications

### FR-NOT-1 — Multi-channel notifications with preferences `[M][Phase 1]`
**Story:** As a director, I want notifications on my preferred channels, so that I don't miss governance events.
**AC:**
- Given channels (email, SMS, push, in-portal), Then I can set per-event preferences.
- Given events (pack published/updated, meeting reminders 7d/1d/1h, resolution awaiting signature, action overdue, conflict declaration required, compliance deadline), Then the right recipients are notified.
- Given email, Then it contains only a link into the Portal, never the confidential content (P5).

### FR-NOT-2 — Announcements with read receipts `[S][Phase 2]`
**Story:** As a Chairman, I want to post board circulars and see who has read them, so that I know the board is informed.
**AC:**
- Given an announcement/pack, When directors open it, Then read receipts show who has/hasn't, visible to Chairman/Cosec.

### FR-NOT-3 — Secure messaging (policy-gated) `[C][Phase 3]`
**Story:** As a director, I want secure in-portal messaging, so that governance discussion stays off personal channels.
**AC:**
- Given messaging is enabled by policy, Then directors can message within scope; Given it's disabled (discoverability policy), Then the feature is hidden. *(Default: off — see §19.)*

---

## 16. Search, dashboards & reporting

### FR-RPT-1 — Global permission-scoped search `[M][Phase 2]`
**Story:** As any user, I want one search across meetings, papers, minutes, resolutions, actions, and people, so that I find things fast — but only what I'm allowed to see.
**AC:**
- Given a query, Then results span all content types, scoped to my permissions, with source links.

### FR-RPT-2 — Role dashboards `[M][Phase 1]`
**Story:** As each role, I want a dashboard tuned to my needs, so that I see what matters on login.
**AC:**
- Given I'm a Chairman, Then I see attendance, overdue actions, upcoming meetings.
- Given I'm a Cosec, Then I see compliance RAG, pack status, and my signature queue.
- Given I'm a director, Then I see my meetings, my actions, and items awaiting my signature.

### FR-RPT-3 — Regulator-ready exports `[M][Phase 2]` `[REG:CAMA]`
**Story:** As a Company Secretary, I want one-click exports of statutory records, so that I can respond to regulators and auditors.
**AC:**
- Given a record type (minute book, resolution register, attendance register, audit-log extract), When I export, Then it produces a dated, entity-branded PDF/Excel.

### FR-RPT-4 — Annual-report governance disclosures `[C][Phase 3]`
**Story:** As a Company Secretary, I want auto-generated governance disclosures, so that annual-report prep is faster.
**AC:**
- Given a period, Then the system generates meetings-held counts, attendance tables, and committee composition.

---

## 17. Audit, security & non-functional requirements

### NFR-AUD-1 — Immutable, tamper-evident audit log `[M][Phase 1]` `[REG:NDPA]`
**Story:** As a Company Secretary/Auditor, I want a complete, tamper-evident log of all content access and changes, so that we can prove who did what.
**AC:**
- Given any event (view, download, print, edit, share, sign, login, permission change, break-glass), Then it is recorded with actor, action, target, timestamp, and IP/device.
- Given the log, Then entries are append-only and hash-chained so tampering is detectable.
- Given a request, Then the log is exportable and filterable by entity, user, and date.

### NFR-SEC-1 — Authentication `[M][Phase 1]`
- **AC:** MFA is mandatory (TOTP + fallback). SSO via Google/Microsoft Entra is supported. Sessions time out; concurrent-session control and optional IP allowlisting are configurable per entity.

### NFR-SEC-2 — Encryption & key management `[M][Phase 1]` `[REG:NDPA]`
- **AC:** Data is encrypted in transit (TLS 1.2+) and at rest. "Crown jewels" papers support per-document encryption. Key management and rotation are documented.

### NFR-SEC-3 — Data residency & privacy `[M][Phase 1]` `[REG:NDPA]`
- **AC:** Data residency is configurable to meet NDPA; personal data handling supports subject-rights requests; no personal/sensitive data is placed in URLs or query strings.

### NFR-SEC-4 — Admin/content separation `[M][Phase 1]`
- **AC:** Platform admins cannot silently read board content; any admin content access is via logged break-glass (see FR-RBAC-3).

### NFR-REL-1 — Backup & disaster recovery `[M][Phase 2]`
- **AC:** Backups run on a defined schedule with tested RPO/RTO. A disaster mode provides read-only access to critical records.

### NFR-PERF-1 — Performance & bandwidth `[S][Phase 2]`
- **AC:** Pack open time on a typical tablet over 3G is acceptable (target: first page < 3s with progressive load). A low-bandwidth mode reduces payloads.

### NFR-A11Y-1 — Accessibility `[S][Phase 2]`
- **AC:** Font scaling and high-contrast modes are available (older directors); the reader meets WCAG 2.1 AA for core flows.

### NFR-MOB-1 — Mobile & offline `[S][Phase 2]`
- **AC:** iOS/Android apps support offline packs, biometric unlock, and remote wipe; tablet reading is first-class.

### NFR-INT-1 — Integrity of the record over time `[M][Phase 2]`
- **AC:** Signed artifacts (minutes, resolutions) remain verifiable via stored hashes even after personnel changes.

### AI Governance & Trust (cross-cutting) — apply to *every* AI feature in §19

> These are threaded through the product the way security is: they are not optional add-ons to individual AI features, they are the conditions under which **any** AI feature is allowed to exist. If a feature in §19 cannot meet all seven, it does not ship. This is what keeps the assistant bounded — deliberately **not** "Super AI."

### NFR-AI-1 — Human-in-the-loop; no autonomous action `[M][ships-with-first-AI-feature]`
- **AC:** No AI feature may sign, vote, approve, publish, distribute, file, alter, or delete any record. Its output is always a *proposal* a human must accept, edit, or reject.
- **AC:** Any state change that follows from an AI suggestion is attributed to the **human** who confirmed it, not to the AI, and is logged as such.

### NFR-AI-2 — Provenance & explainability `[M][ships-with-first-AI-feature]` `[REG:NDPA]`
- **AC:** Every AI output answers, in-context: **why am I seeing this**, **based on what sources**, **how confident**, and **what should I verify** (per Design Language Ch. 24).
- **AC:** Cited sources link back to the exact document/page/record the output was drawn from; unsupported output is not shown.

### NFR-AI-3 — Permission-scoped; no cross-entity leakage `[M][ships-with-first-AI-feature]`
- **AC:** An AI feature operates strictly within the requesting user's existing permission scope; it can never surface content the user could not otherwise open.
- **AC:** No prompt, retrieval, summary, or answer may cross an entity boundary. Recused agenda items are invisible to AI for that user too.

### NFR-AI-4 — Data isolation & no-training guarantee `[M][ships-with-first-AI-feature]` `[REG:NDPA]`
- **AC:** Governance content is never used to train third-party models and never leaves the contracted processing boundary; the data-isolation guarantee is contractual and evidenced.
- **AC:** Data residency rules (NFR-SEC-3) apply equally to any AI processing path.

### NFR-AI-5 — Per-feature enablement & policy control `[M][ships-with-first-AI-feature]`
- **AC:** Every AI feature is **off by default** and enabled per entity by an authorized admin/Company Secretary; a global kill-switch disables all AI instantly.
- **AC:** The enablement state and who changed it are logged and visible in Portal Settings.

### NFR-AI-6 — Full audit logging of AI `[M][ships-with-first-AI-feature]`
- **AC:** Every AI invocation (who, when, feature, inputs referenced, output produced, and the human disposition — accepted/edited/rejected) is written to the immutable audit log (NFR-AUD-1).

### NFR-AI-7 — Always identifiable, never disguised `[M][ships-with-first-AI-feature]`
- **AC:** AI-generated content is always visually distinct (the AI treatment / "AI Insight" label and AI color tokens from the Design Language), never presented as if authored by a person, and always dismissible without trapping focus (Design Language Ch. 24, Ch. 37).

---

## 18. Administration & platform

### FR-ADM-1 — Portal & entity settings `[M][Phase 1]`
**Story:** As an administrator, I want configurable settings per entity, so that each company reflects its own branding and rules.
**AC:**
- Given an entity, Then I can set branding, agenda/minutes/pack templates, resolution numbering scheme, retention policies, and notification policies.

### FR-ADM-2 — User lifecycle & bulk import `[M][Phase 1]`
**Story:** As an administrator, I want to onboard/offboard users and bulk-import, so that user management scales.
**AC:**
- Given onboarding, Then invitation, induction-pack delivery, and scoped access provisioning occur; Given offboarding, Then access is revoked while history is preserved (P6).

### FR-ADM-3 — Integrations & API `[C][Phase 3]`
**Story:** As an administrator, I want an API and webhooks, so that the Portal integrates with HRIS, DMS, e-signature, and calendar/Exchange.
**AC:**
- Given the API, Then core objects (entities, meetings, documents, resolutions, users) are accessible with scoped auth; webhooks fire on key events.

### FR-ADM-4 — Sandbox/training environment `[C][Phase 3]`
**Story:** As an administrator, I want a training sandbox, so that new directors learn without touching live data.
**AC:**
- Given the sandbox, Then it mirrors production features with isolated, disposable data.

---

## 19. AI-assist layer (bounded assistant — policy-gated)

> **What this is — and isn't.** This is the group's most sensitive corpus, so the assistant is deliberately **bounded**: it *drafts, summarizes, surfaces, finds, and explains*, and then hands off to a human. It is **not** an autonomous agent — it does not sign, vote, approve, publish, file, alter, or delete anything, and it takes no action on the record on its own (P10). Every feature below inherits the **AI Governance & Trust** requirements (NFR-AI-1…7): off by default, human-in-the-loop, permission-scoped, explainable, isolated, logged, and always identifiable. A feature that can't meet all seven does not ship.
>
> **Scope note:** this section is the product's *in-app* AI. It is separate from any developer tooling (e.g., Claude Code) used to *build* the Portal — build-time tooling is not part of the product and is governed by engineering practice, not this section.

**Explicitly out of scope (the "not Super AI" line):** auto-approving or auto-signing anything; casting or changing votes; auto-publishing packs or minutes; auto-filing to regulators; making governance decisions or recommendations that bypass a human; acting across entity boundaries; or operating without an audit trail. These are permanent non-goals, not deferred features.

### Assistive features

### FR-AI-1 — Minutes drafting assist `[C][Phase 3]`
**Story:** As a Company Secretary, I want a first-draft of minutes from a meeting transcript, so that I write minutes faster.
**AC:** Given a transcript and consent, When I request a draft, Then the system proposes item-by-item minutes for my editing; nothing is finalized or adopted without my action; provenance and the action are logged (NFR-AI-2, NFR-AI-6).

### FR-AI-2 — Pack summarization & "ask the pack" `[C][Phase 3]`
**Story:** As a director, I want per-item summaries and to ask questions of a board pack, so that I prepare faster.
**AC:** Given a pack, Then summaries and scoped Q&A are available only to users entitled to that pack; answers cite source pages; no cross-entity leakage (NFR-AI-3); recused items are excluded.

### FR-AI-3 — Resolution drafting from precedent `[C][Phase 3]`
**Story:** As a Company Secretary, I want a resolution drafted from prior precedent, so that I start from a proven form.
**AC:** Given a request, Then a draft is proposed from precedent **within the same entity's** permission scope, for my editing; it is never numbered, passed, or circulated by the AI.

### FR-AI-4 — Attention surfacing on dashboards `[C][Phase 3]`
**Story:** As a Chairman/Company Secretary, I want the assistant to surface what needs attention, so that nothing important is missed.
**AC:** Given my role and scope, Then AI may highlight read-only signals (e.g., directors who haven't opened a pack, overdue actions, quorum risk) as dismissible "AI Insight" cards; each states why and links to the source; it never sends reminders or takes action itself — it offers the human a one-click *human-initiated* action.

### FR-AI-5 — Matters-arising & action suggestions `[C][Phase 3]`
**Story:** As a Company Secretary, I want suggested action items and matters-arising drawn from minutes, so that follow-through is captured.
**AC:** Given adopted minutes, Then the assistant proposes candidate actions/owners/dates for my confirmation; suggestions are inert until I accept them.

### FR-AI-6 — Compliance & deadline nudges `[C][Phase 3]` `[REG:CAMA][REG:CBN]`
**Story:** As a Company Secretary, I want the assistant to flag approaching statutory deadlines and gaps, so that filings aren't missed.
**AC:** Given the compliance calendar (§12), Then AI may surface at-risk obligations and missing register data as explained insights; it never files, and never changes a status on its own.

### FR-AI-7 — Conflict-of-interest hinting `[C][Phase 3]`
**Story:** As a Company Secretary, I want the assistant to hint at possible conflicts between an agenda and the interests register, so that declarations aren't overlooked.
**AC:** Given a published agenda and the register of interests (§10), Then AI may hint "director X may have an interest in item N" for **human confirmation**; it never records a conflict or enforces recusal itself — that remains a human/system action (FR-CONF-2).

### FR-AI-8 — Semantic search across the record `[C][Phase 3]`
**Story:** As any user, I want to find things in my own words across the record, so that I don't need exact keywords.
**AC:** Given a natural-language query, Then results are permission-scoped (NFR-AI-3), cite their sources, and are read-only; this augments — not replaces — the deterministic search in FR-RPT-1.

---

## 20. Data model (high-level)

Core entities and key relationships (indicative, not the schema):

- **Organization/Group** 1—N **Entity** (self-referential tree via `parent_entity_id`).
- **Entity** 1—N **Committee**, **Meeting**, **Document**, **Resolution**, **Register**, **RoleAssignment**, **ComplianceObligation**.
- **Person** 1—N **RoleAssignment** (scoped to Entity/Committee/Meeting).
- **Meeting** 1—N **AgendaItem**; **AgendaItem** 1—N **Document (paper)**; **Meeting** 1—1 **Pack (versioned)**; **Meeting** 1—1 **Minutes**; **Meeting** 1—N **Attendance**, **Action**, **Resolution**, **Vote**.
- **Resolution** N—N **Signature** (for circular resolutions); **Resolution** 1—N **CTC issuance**.
- **Document** 1—N **Version**, 1—N **Annotation**, 1—N **AccessEvent (audit)**.
- **AuditEvent** references any object; append-only, hash-chained.
- **ConflictDeclaration** links **Person** × **AgendaItem** and drives access/vote exclusion.

`DM-2`: Every content object carries entity scope; every read/write emits an `AuditEvent`. There is no un-scoped content object.

---

## 21. Rollout plan (phasing)

**Phase 1 — MVP spine (system of record for one board, security-complete).**
RBAC (scoped, break-glass), Entity profile, Meetings (calendar, notice, agenda, pack, attendance/quorum), Documents (library, versioning, watermark, download control), Minutes (draft→approve), Resolutions (in-meeting, circular, CTC), Actions (capture), Notifications (multi-channel), Role dashboards, Portal/entity settings, User lifecycle. **Security from day one:** audit log, MFA/SSO, encryption, residency, admin/content separation.

**Phase 2 — Multi-entity + governance depth.**
Group vs entity views, statutory registers, in-meeting mode, virtual integration, annotations, offline packs, immutable minute book & matters arising, resolution register & thresholds/DoA, conflicts/interests registers, committees & reporting, compliance calendar & filing tracker, actions escalation/dashboards, global search, regulator exports, DR/backup, performance/a11y/mobile.

**Phase 3 — Optimization, evaluation, AI, integrations.**
Intercompany governance, AGM/EGM, group committees, related-party/gifts/attestations, policy library, regulatory correspondence, board evaluation/skills/succession/CPD, announcements & (policy-gated) messaging, annual-report disclosures, API/webhooks, sandbox, and the **bounded AI-assist layer** (§19, FR-AI-1…8).

**Sequencing rules:** (a) the multi-entity data model exists in Phase 1 even though group UI lands in Phase 2; (b) audit + MFA + encryption are non-deferrable; (c) CTC and circular resolutions are pulled early (high real-world value, low cost); (d) **AI is last on purpose** — the record-of-truth, permissions, and audit log must be mature *before* any assistant reads from them, and the moment the first AI feature ships, the entire AI Governance & Trust block (NFR-AI-1…7) ships with it — those guardrails are never deferred behind the features they govern.

---

## 22. Open questions (for the design/UX session and stakeholders)

1. **Entity scope at launch** — do we ship single-entity UI first (Liberty Pay) with the multi-entity model behind it, or expose the group tree immediately?
2. **Secure messaging** — on or off by default, given legal-discoverability concerns?
3. **Data residency** — is Nigeria-hosted mandatory now, or acceptable to host offshore with NDPA controls initially? (Affects infra on `libertyapp-01` vs cloud.)
4. **E-signature** — build native or integrate (DocuSign/Adobe)? Affects legal weight and cost.
5. **Statutory notice periods** — confirm the exact CAMA/articles notice rules per meeting type to encode.
6. **Numbering schemes** — confirm resolution/minute numbering conventions per entity.
7. **CAC filing** — track-only for now, or pursue direct integration later?
8. **AI-assist** — is there appetite/policy clearance to pilot minutes-drafting, or hold entirely for Phase 3?
9. **Mobile** — native apps vs responsive PWA for the offline reading experience?
10. **DoA matrix** — does a delegated-authority matrix already exist to encode, or do we design it here?

---

## 23. Glossary

- **CAMA 2020** — Companies and Allied Matters Act (Nigeria).
- **CAC** — Corporate Affairs Commission (Nigerian company registry).
- **CBN** — Central Bank of Nigeria.
- **NDPA** — Nigeria Data Protection Act 2023.
- **CTC** — Certified True Copy (of a resolution/document).
- **DoA** — Delegation of Authority.
- **PSC / Beneficial Ownership** — Persons with Significant Control register.
- **Pack / Board Pack** — compiled set of papers for a meeting.
- **Circular/Written Resolution** — resolution passed by signature between meetings.
- **Quorum** — minimum attendance for a valid meeting.
- **RAG** — Red/Amber/Green status.
- **RPO/RTO** — Recovery Point/Time Objective.

---

*End of PRD v0.1. Next: design language & UX system, referencing the FR/NFR IDs above.*
