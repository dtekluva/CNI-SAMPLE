# Northstar Product Language — Volume V: Components

**Product:** CNI Group Governance Portal
**Status:** Draft v1.0
**Prepared:** 2026-07-17
**Depends on:** [NORTHSTAR_TOKENS.md](NORTHSTAR_TOKENS.md) (Vol IV). Live: [components.css](components.css) · [components.html](components.html).

> **The rule of this volume (Vol IV, Ch. 27):** a component is a *composition of primitives*, never a new invention. Every component here reads only semantic tokens (`--ns-color-*`, `--ns-space-*`, …). No component introduces a raw hex, px, or duration. Change a token → every component moves. That is why the whole gallery re-themes (Light / Dark / High-Contrast) with zero markup change — verified.

Each component is documented with the canonical anatomy: **Purpose · Anatomy · States · Behavior · Accessibility · AI integration · Morphology · Anti-patterns · Engineering**.

---

## Component index

**Primitives:** Button · Badge/Status pill · Field/Input · Card
**Governance-specific:** Approval Card · AI Insight Panel · Audit/Decision Timeline · Workspace Shell

Roadmap (next): Data Table (with compact density), Pack Reader, Agenda Builder row, Signature block, Conflict banner, Empty/Loading/Error states as shared partials, Toast, Modal, Drawer, Command palette / global search.

---

## 1. Button

**Purpose.** Trigger an action. Hierarchy communicates consequence — the design language leans on *one* primary per view (Ch. 17: one dominant purpose per screen).

**Anatomy.** `[optional icon] label [optional icon]` inside a token-sized pill (`radius.medium`, `weight.semibold`, `body-sm`). Optional leading spinner for the loading state.

**Variants (hierarchy).**
| Variant | Use | Token base |
|---|---|---|
| `--primary` | The one main action (Publish, Confirm) | `color.primary` / `on.primary` |
| `--secondary` | Alternatives (Save draft, Cancel-with-weight) | `surface` + `border.default` |
| `--ghost` | Low-emphasis / tertiary (Cancel, dismiss) | transparent → `surface.hover` |
| `--danger` | Destructive/irreversible (Revoke, Delete) | `danger.fill` / `danger.on` |
| `--ai` | AI-initiated drafting only | `ai.fill` / `on.ai` |

**Sizes:** `--sm` 32px · default 40px · `--lg` 48px. All meet the 44px touch target via padding on touch (or use `--lg` on mobile).

**States.** default · hover · active/pressed · focus-visible (token focus ring) · disabled (`opacity.disabled`, not-allowed) · loading (spinner + label, stays same width, disabled while pending).

**Behavior.** Loading disables re-submit. Danger actions that are irreversible require confirmation (per the global safety posture) — the button opens a confirm, it doesn't fire immediately.

**Accessibility.** Real `<button>`; label is text (icon-only buttons need `aria-label`); focus ring never removed; disabled uses `aria-disabled` + not-allowed, still discoverable by SR.

**AI integration.** `--ai` is reserved for *human-initiated* AI drafting (e.g., "Draft with AI"). It never appears on an action the AI performs itself — AI proposes, the human's normal primary/secondary buttons dispose (P10).

**Morphology.** Mobile: prefer `--block` full-width stacked; group primary bottom. Desktop: inline, primary right-most in a footer.

**Anti-patterns.** ✗ Two primaries in one view. ✗ Danger styling for non-destructive actions. ✗ Color-only distinction between primary and danger (they also differ by position/label).

**Engineering.** `.ns-btn` + one variant + optional `--sm/--lg/--block`. Spinner = `.ns-btn__spinner`.

---

## 2. Badge / Status pill

**Purpose.** Communicate state at a glance. This is *the* place color = meaning (Vol III Ch. 19) does the most work.

**Anatomy.** `[dot] label` in a `radius.full` pill, `caption` weight-semibold, semantic subtle bg + semantic text token.

**Variants:** `neutral` (Draft) · `success` (Approved/Passed) · `warning` (Awaiting/Pending) · `danger` (Overdue/Breach) · `info` (For noting) · `ai` (AI drafted).

**Accessibility (critical).** Color is **never** the only signal — every badge carries a text label, and the leading dot is decorative. This is the rule that makes the product usable for color-blind directors. The amber caution from Vol IV holds: warning uses `warning.text` on `warning.subtle`, never white on amber.

**AI integration.** The `ai` badge marks content the assistant drafted, so provenance is visible in lists, not just in panels.

**Anti-patterns.** ✗ Badge with no label. ✗ Inventing a new color for a new status — map it to one of the six meanings. ✗ Using `danger` for "important but fine."

**Engineering.** `.ns-badge .ns-badge--<variant>` with an optional `.ns-badge__dot`.

---

## 3. Field / Input

**Purpose.** Collect one value with label, hint, and error in a predictable stack.

**Anatomy.** `label → control → hint | error`. Control is 40px, `radius.medium`, `border.default`.

**States.** default · hover (`border.strong`) · focus (`border.focus` + ring) · invalid (`aria-invalid` → `danger.fill` border + `field__error`) · disabled.

**Behavior.** Governance example shown in the gallery: a notice-period below the statutory minimum flips to invalid with a *remedial* message ("record consent to short notice") — errors explain the fix, never blame (Vol IV Ch. 35).

**Accessibility.** `<label for>` bound; `aria-invalid` + `aria-describedby` to the error; hint text is programmatically associated; error is text + color, never color alone.

**Anti-patterns.** ✗ Placeholder as label. ✗ Red border with no message. ✗ Blaming copy ("Invalid input").

**Engineering.** `.ns-field` wrapper; `.ns-input` control; `[aria-invalid="true"]` drives the error styling.

---

## 4. Card

**Purpose.** The base surface. Groups related content with a border and *minimal* shadow (Ch. 31: borders over shadows).

**Anatomy.** optional `__header` · `__body` · optional `__footer` (right-aligned actions). `radius.large`, `elevation.1`.

**Behavior.** Cards don't nest more than one level deep (Vol IV Ch. 30: two surfaces beat five).

**Engineering.** `.ns-card` + `__header/__body/__footer`. `.ns-overline` and `.ns-mono` are shared text partials.

---

## 5. Approval Card  ⭐ governance-specific

**Purpose.** Represent **a decision awaiting a human** — the atomic unit of governance. A resolution to vote on, a circular resolution to sign, minutes to adopt. It is the component that embodies *Decisions Over Records*.

**Anatomy.**
- Left **status accent** (3px border) — the fastest read of where the decision stands (amber pending · green approved · red rejected).
- `__top`: overline (type + auto-number, e.g. `LP/BD/2026/014` in mono) + title + a status **badge**.
- `__meta`: mover, seconder, closing time (governance provenance).
- `__tally`: For / Against / Abstain / Recused, big tabular numbers, semantically colored.
- `__actions`: the human's decision buttons, on a subtle footer.

**States.** pending (awaiting your action — emphasized) · approved/passed · rejected/lapsed · not-yet-open · closed. The card *itself* never changes state autonomously — a human action or a tallied vote does.

**Behavior.** Recused directors don't see the tally-affecting controls (ties to FR-RBAC-2 / FR-VOTE-2). Irreversible actions (cast vote, sign) confirm first. Every action writes to the audit timeline.

**Accessibility.** Status is conveyed by badge text + accent + tally, never accent color alone. Actions are real buttons with clear labels. Tally uses `tabular-nums` so numbers align.

**AI integration.** An AI Insight panel may sit *beside or above* an Approval Card (e.g., a conflict hint on the related item), but AI never populates the tally, never casts or changes a vote, and never moves the card to approved/rejected. It informs the human who then acts.

**Morphology.** Desktop: two-up grid. Mobile: full-width stacked; actions become `--block`.

**Anti-patterns.** ✗ Auto-approving on a threshold without the human's recorded action where a vote is required. ✗ Hiding who moved/seconded. ✗ Using the accent color as the only status signal.

**Engineering.** `.ns-approval .ns-approval--<status>` → `__top / __meta / __tally / __actions`.

---

## 6. AI Insight Panel  ⭐ governance-specific · the heart of "Visual AI" (Ch. 24)

**Purpose.** Present an AI-generated observation, summary, or hint **as a proposal**, with full provenance, and hand off to a human. This is where the design language's AI posture becomes a component.

**Anatomy.**
- Distinct AI surface: `ai.subtle` bg + `ai.border` — recognizably AI, never louder.
- `__tag`: the **"AI Insight"** label + purple glyph — always present, so AI is never disguised (NFR-AI-7).
- `__body`: the insight, in plain language.
- `__prov`: **provenance row** answering the four Ch. 24 questions — *based on what* (sources, linked), *how confident* (a confidence meter), and a *"Why am I seeing this?"* link. *What to verify* is implied by the human-action framing.
- `__actions`: human dispositions (Confirm / Dismiss / Send reminder) — all **human-initiated**.
- `__dismiss`: always dismissible (×), never traps focus (Ch. 37).

**Variants.** Informational insight (attention surfacing, FR-AI-4) · Conflict hint (FR-AI-7) · Summary ("ask the pack", FR-AI-2). Same shell, different body + actions.

**States.** default · dismissed · low/medium/high confidence (meter width) · loading (skeleton, per Ch. 35 — never a bare spinner).

**Behavior.** The panel *suggests*; the human's buttons *act*. "Send reminder" is a one-click human-initiated action, not something the AI does on its own. Dismissing is logged (NFR-AI-6). Nothing here signs, votes, files, or publishes.

**Accessibility.** `role="note"` with an `aria-label`; dismiss has an `aria-label`; the confidence meter has a text equivalent ("confidence: high"); purple is reinforced by the "AI Insight" text so it's not color-only; focus never trapped.

**AI integration.** This *is* the AI integration surface. Every other component that surfaces AI (a badge, a context-panel snippet) uses this panel's language: purple treatment + "AI Insight" label + provenance.

**Morphology.** Desktop: full-width stack or condensed inside the context panel. Mobile: full-width; provenance wraps.

**Anti-patterns.** ✗ AI content that looks author-written (no tag). ✗ Recommendation with no source/confidence. ✗ A non-dismissible or focus-trapping panel. ✗ An AI button that performs a governance action directly. ✗ Using purple for urgency instead of provenance.

**Engineering.** `.ns-ai` → `__tag / __body / __prov (__conf) / __actions / __dismiss`. Confidence meter is `.ns-ai__conf .bar > i[style=width]` + a text label.

---

## 7. Audit / Decision Timeline

**Purpose.** The tertiary "history" layer (Vol III Ch. 18) — an immutable, chronological record of what happened. Backs the audit log and a resolution's decision history.

**Anatomy.** Vertical rail; each item = a status dot (`success/info/danger/neutral`) + actor (bold) + action + right-aligned timestamp (mono/tabular, `text.tertiary`).

**Behavior.** Read-only. Break-glass and other high-severity events use the `danger` dot so they stand out in the stream. Entries never edit or delete (P4 — append-only).

**Accessibility.** Ordered list semantics (`<ul>`/`<ol>`); dot color reinforced by text; timestamps have accessible absolute values.

**Anti-patterns.** ✗ Editable history. ✗ Dot color as the only signal of severity.

**Engineering.** `.ns-timeline > .ns-timeline__item` with `.ns-timeline__dot--<variant>`.

---

## 8. Workspace Shell

**Purpose.** The three-region desktop frame (Vol IV Ch. 29): **sidebar (navigation) · workspace (the work) · context panel (related + AI)**. Realizes *Context Before Navigation* — related entities and AI ride alongside the task instead of behind a click.

**Anatomy.** `nav` (brand + nav items, active state in `primary.subtle`) · `work` (the primary task, one dominant purpose) · `ctx` (context: related papers, AI Insight, quick actions).

**Behavior.** Context panel is where AI Insight lives during a task — a conflict hint next to the agenda, a summary next to the pack. The workspace holds one thought per screen (Vol III interaction principle).

**Morphology (adaptive, not shrinking — Ch. 29).** Desktop ≥900px: 3 regions (`240px · 1fr · 300px`, verified). Tablet: 2 regions (context collapses to a toggle). Mobile <900px: single column, nav → bottom/drawer, context → inline or sheet. New info *appears* rather than the layout stretching.

**Accessibility.** Landmarks (`nav`, `main`, `aside`); logical focus order sidebar → workspace → context; nav items are links with a visible active state (not color-only — active also changes weight/background).

**Anti-patterns.** ✗ Forcing users to leave the workspace to see related context. ✗ Three primary actions competing in the workspace. ✗ Shrinking the desktop layout onto mobile instead of reflowing.

**Engineering.** `.ns-shell` grid → `__nav / __work / __ctx`; single-column under 900px.

---

## Cross-cutting: shared states (Vol IV Ch. 35)

Every component inherits the state model. Two that need shared partials next:
- **Empty state** — explains *why nothing's here*, *what happens next*, and *how AI can help* (never a blank void).
- **Loading** — skeletons that preserve layout, never bare spinners (except the in-button micro-spinner).
- **Error** — explains what happened + what's retryable, never blames the user.

---

## Verification (2026-07-17)

Built live and checked in-browser: no console errors; Button (all variants/sizes/loading/disabled), Badge (6 meanings), Field (incl. invalid), Approval Card (pending/approved), AI Insight (info + conflict-hint), Timeline (4 severities), and Workspace Shell all render from tokens. Theme flip verified Light ↔ Dark ↔ High-Contrast with **zero markup change**. Shell grid resolves `240px 514px 300px` at desktop and collapses to single-column below 900px.

*Next (Vol VI — Enterprise Patterns): assemble these components into the governance workspaces named in the PRD — Board Meeting, Resolution, Committee, Company, Audit, Risk, Compliance — each mapped to its FR/NFR IDs.*
