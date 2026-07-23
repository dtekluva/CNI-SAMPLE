# Northstar Design Tokens — v1.0

**Part of:** Northstar Product Language, Volume IV (Foundations) → concrete values
**Product:** CNI Group Governance Portal
**Status:** Draft v1.0 — first assigned values
**Prepared:** 2026-07-17

> Volume IV named the tokens. This document assigns their **values**. Nothing in the product hard-codes a color, size, radius, or duration — every component reads from these tokens. Change a value here, and the whole system moves with it.

**Two layers.** Tokens come in two tiers:
- **Primitives** — the raw palette and scales (`neutral.500`, `blue.600`, `space.16`). Never referenced directly by components.
- **Semantic aliases** — meaning-bearing tokens (`text.primary`, `color.primary`, `border.focus`) that *point at* primitives and **flip per theme**. Components reference only these.

This indirection is what makes Light / Dark / High-Contrast / Presentation themes possible with **token changes only, never component rewrites** (Ch. 36).

Naming in code uses the `--ns-` prefix (Northstar). Files: [`tokens.json`](tokens.json) (source of truth, tooling), [`tokens.css`](tokens.css) (ready-to-use CSS variables per theme).

---

## 1. Color philosophy → hues

Volume IV Ch. 19 fixed color as *meaning, never decoration*. Each hue below carries exactly the meaning the RFC assigned. The neutral ramp is cool-tinted (a faint blue) — it reads as *precise* and *trustworthy*, and it makes the semantic hues feel intentional rather than loud.

| Meaning (from RFC) | Hue | Role |
|---|---|---|
| Structure, not emphasis | **Neutral (cool slate)** | Text, surfaces, borders — ~90% of every screen |
| Information · navigation · links | **Blue** | Primary actions, links, selection |
| Success · healthy · approved | **Green** | Passed resolutions, quorum met, filed |
| Attention · pending · awaiting review | **Amber** | Draft, awaiting signature, due soon |
| Urgent · risk · violation | **Red** | Overdue, breach, danger actions |
| Artificial intelligence · generated | **Purple** | AI insights, provenance, recommendations |

**Restraint rule:** a governance screen is mostly neutral. Semantic color appears only where it changes a decision — a status, a deadline, a risk. If everything is colored, nothing is.

---

## 2. Primitive color ramps

Each ramp runs 50 (lightest) → 900 (darkest). Contrast notes are **against white `#FFFFFF`** and target **WCAG 2.1 AA** (4.5:1 normal text, 3:1 large text / UI). Run the palette through your contrast checker in tooling before final sign-off — values below are chosen to pass but should be verified in context.

### Neutral (cool slate) — the workhorse
| Token | Hex | Typical use |
|---|---|---|
| `neutral.0` | `#FFFFFF` | Surface / card background (light) |
| `neutral.50` | `#F8FAFC` | Canvas / page background (light) |
| `neutral.100` | `#F1F5F9` | Subtle fills, hover, subtle border |
| `neutral.200` | `#E2E8F0` | **Default border** |
| `neutral.300` | `#CBD5E1` | Strong border, dividers |
| `neutral.400` | `#94A3B8` | Disabled text, placeholder |
| `neutral.500` | `#64748B` | Tertiary text · AA (4.7:1) |
| `neutral.600` | `#475569` | Secondary text · AA (7.0:1) |
| `neutral.700` | `#334155` | Body-strong · AAA |
| `neutral.800` | `#1E293B` | Headings (alt) |
| `neutral.900` | `#0F172A` | **Primary text** · AAA (17:1) |
| `neutral.950` | `#020617` | Max ink / dark-theme canvas base |

### Blue — information & primary
| Token | Hex | Note |
|---|---|---|
| `blue.50` | `#EFF6FF` | Primary-subtle bg, selected row |
| `blue.100` | `#DBEAFE` | |
| `blue.200` | `#BFDBFE` | |
| `blue.300` | `#93C5FD` | Dark-theme border-focus |
| `blue.400` | `#60A5FA` | Dark-theme primary/link |
| `blue.500` | `#3B82F6` | |
| `blue.600` | `#2563EB` | **Primary action fill** · white text AA · focus ring |
| `blue.700` | `#1D4ED8` | **Link text** / primary-hover · AA (6.3:1) |
| `blue.800` | `#1E40AF` | Primary-pressed |
| `blue.900` | `#1E3A8A` | |

### Green — success
| Token | Hex | Note |
|---|---|---|
| `green.50` | `#ECFDF5` | Success-subtle bg (badge) |
| `green.100` | `#D1FAE5` | |
| `green.500` | `#10B981` | Dark-theme accents |
| `green.600` | `#059669` | **Success fill** · white text AA |
| `green.700` | `#047857` | **Success text on white** · AA (4.9:1) |
| `green.800` | `#065F46` | |

### Amber — warning / pending  ⚠ contrast caution
| Token | Hex | Note |
|---|---|---|
| `amber.50` | `#FFFBEB` | Warning-subtle bg (badge) |
| `amber.100` | `#FEF3C7` | |
| `amber.400` | `#FBBF24` | Dark-theme accents |
| `amber.500` | `#F59E0B` | Icon fill on dark |
| `amber.600` | `#D97706` | Warning fill — **use near-black text, not white** |
| `amber.700` | `#B45309` | **Warning text on white** · AA (4.8:1) |
| `amber.800` | `#92400E` | |

> Amber never carries white text at AA. Warning badges = `amber.50` bg + `amber.700` text. Solid amber buttons are discouraged; if used, text is `neutral.900`.

### Red — danger / risk
| Token | Hex | Note |
|---|---|---|
| `red.50` | `#FEF2F2` | Danger-subtle bg |
| `red.100` | `#FEE2E2` | |
| `red.400` | `#F87171` | Dark-theme danger |
| `red.600` | `#DC2626` | **Danger fill** · white text AA |
| `red.700` | `#B91C1C` | **Danger text on white** · AA (5.9:1) |
| `red.800` | `#991B1B` | Danger-pressed |

### Purple — AI
| Token | Hex | Note |
|---|---|---|
| `purple.50` | `#F5F3FF` | **AI-subtle** bg (insight panels) |
| `purple.100` | `#EDE9FE` | |
| `purple.200` | `#DDD6FE` | AI border |
| `purple.400` | `#A78BFA` | Dark-theme AI |
| `purple.600` | `#7C3AED` | **AI accent fill** · white text AA |
| `purple.700` | `#6D28D9` | **AI text on white** · AA (6.1:1) |
| `purple.900` | `#4C1D95` | |

---

## 3. Semantic aliases (light theme)

Components reference **only** these. Each maps to a primitive; §7 shows how they flip for dark/high-contrast.

### Surfaces & background
| Alias | → primitive | Value |
|---|---|---|
| `color.canvas` | neutral.50 | `#F8FAFC` |
| `color.bg.secondary` | neutral.100 | `#F1F5F9` |
| `color.surface` | neutral.0 | `#FFFFFF` |
| `color.surface.subtle` | neutral.50 | `#F8FAFC` |
| `color.surface.hover` | neutral.100 | `#F1F5F9` |
| `color.surface.selected` | blue.50 | `#EFF6FF` |
| `color.overlay.scrim` | — | `rgba(15,23,42,0.45)` |

### Text
| Alias | → primitive | Value | Contrast on surface |
|---|---|---|---|
| `color.text.primary` | neutral.900 | `#0F172A` | AAA |
| `color.text.secondary` | neutral.600 | `#475569` | AA (7:1) |
| `color.text.tertiary` | neutral.500 | `#64748B` | AA (4.7:1) |
| `color.text.disabled` | neutral.400 | `#94A3B8` | decorative only |
| `color.text.inverse` | neutral.0 | `#FFFFFF` | on dark fills |
| `color.text.link` | blue.700 | `#1D4ED8` | AA |

### Border
| Alias | → primitive | Value |
|---|---|---|
| `color.border.subtle` | neutral.100 | `#F1F5F9` |
| `color.border.default` | neutral.200 | `#E2E8F0` |
| `color.border.strong` | neutral.300 | `#CBD5E1` |
| `color.border.focus` | blue.600 | `#2563EB` |

### Primary (interactive)
| Alias | → primitive | Value |
|---|---|---|
| `color.primary` | blue.600 | `#2563EB` |
| `color.primary.hover` | blue.700 | `#1D4ED8` |
| `color.primary.pressed` | blue.800 | `#1E40AF` |
| `color.primary.subtle` | blue.50 | `#EFF6FF` |
| `color.on.primary` | neutral.0 | `#FFFFFF` |

### Semantic status (each: `.fill` for solid, `.subtle` for badge bg, `.text` for text/icon on white)
| Meaning | `.fill` | `.subtle` | `.text` | `.on` (text on fill) |
|---|---|---|---|---|
| **success** | `#059669` | `#ECFDF5` | `#047857` | `#FFFFFF` |
| **warning** | `#D97706` | `#FFFBEB` | `#B45309` | `#0F172A` |
| **danger** | `#DC2626` | `#FEF2F2` | `#B91C1C` | `#FFFFFF` |
| **info** | `#2563EB` | `#EFF6FF` | `#1D4ED8` | `#FFFFFF` |

### AI (distinct treatment — Ch. 24)
| Alias | → primitive | Value |
|---|---|---|
| `color.ai.fill` | purple.600 | `#7C3AED` |
| `color.ai.subtle` | purple.50 | `#F5F3FF` |
| `color.ai.text` | purple.700 | `#6D28D9` |
| `color.ai.border` | purple.200 | `#DDD6FE` |
| `color.on.ai` | neutral.0 | `#FFFFFF` |

> **AI usage rule (Ch. 24):** AI surfaces use `ai.subtle` background + `ai.border` + an "AI Insight" label. Purple signals *provenance*, not importance — never use it to make something look more urgent.

---

## 4. Typography

**Families.** Governance mixes three needs: scannable UI, long-form reading (board papers), and precise figures (resolution numbers, audit hashes, amounts).

| Token | Stack | Use |
|---|---|---|
| `font.family.primary` | `"Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` | All UI, headings, labels |
| `font.family.reading` | `"Source Serif 4", Georgia, "Times New Roman", serif` | Long-form board-paper body (optional, opt-in per document) |
| `font.family.mono` | `"JetBrains Mono", ui-monospace, "SF Mono", Menlo, monospace` | Resolution IDs, hashes, amounts, tabular figures |

**Weights:** `regular 400` · `medium 500` · `semibold 600` · `bold 700`. Northstar leans on **500/600 for hierarchy**, rarely 700 (Ch. 20 — typography, not weight, carries hierarchy).

**Scale.** Base is **16px** (1rem) — deliberately generous; the RFC calls out older directors and font scaling (Ch. 37). Sizes in rem so browser zoom / user scaling works.

| Token | Size (px / rem) | Line-height | Weight | Use |
|---|---|---|---|---|
| `font.size.display` | 36 / 2.25 | 44px (1.22) | 700 | Dashboard hero ("Good morning, …") |
| `font.size.page` | 28 / 1.75 | 36px (1.29) | 700 | Page title |
| `font.size.heading` | 22 / 1.375 | 30px (1.36) | 600 | Section heading |
| `font.size.subheading` | 18 / 1.125 | 26px (1.44) | 600 | Card title, sub-section |
| `font.size.body-lg` | 17 / 1.0625 | 28px (1.65) | 400 | Reading / pack body |
| `font.size.body` | 16 / 1.0 | 26px (1.625) | 400 | **Default body** |
| `font.size.body-sm` | 14 / 0.875 | 22px (1.57) | 400 | Dense tables, secondary |
| `font.size.caption` | 13 / 0.8125 | 18px (1.38) | 500 | Metadata, timestamps |
| `font.size.label` | 12 / 0.75 | 16px (1.33) | 600 | Overline labels, `+0.04em`, UPPERCASE |

**Letter-spacing:** `tracking.tight -0.01em` (display/page) · `tracking.normal 0` · `tracking.label +0.04em` (labels/overline).

**Figures:** anything numeric that aligns in columns (amounts, vote tallies, dates in tables) uses `font-variant-numeric: tabular-nums` — or `font.family.mono` for IDs/hashes.

---

## 5. Spatial system (8-pt)

Ch. 28 — 8-pt base, consistency over mathematical completeness. Named steps map to the RFC's scale:

| Token | px | rem | Typical use |
|---|---|---|---|
| `space.0` | 0 | 0 | reset |
| `space.3xs` | 4 | 0.25 | icon↔label, inline gaps |
| `space.2xs` | 8 | 0.5 | tight stacks, chip padding |
| `space.xs` | 12 | 0.75 | control inner padding |
| `space.sm` | 16 | 1.0 | default gap, card padding (compact) |
| `space.md` | 24 | 1.5 | card padding, section inner gap |
| `space.lg` | 32 | 2.0 | between sections |
| `space.xl` | 48 | 3.0 | major section breaks |
| `space.2xl` | 64 | 4.0 | page region separation |
| `space.3xl` | 96 | 6.0 | hero / empty-state breathing room |

**Rule of rhythm (Ch. 28):** vertical space builds reading rhythm; horizontal space signals relationship. Grouped = close; independent = spaced. Structure is read from space, not borders.

---

## 6. Radius, elevation, motion, layering

### Radius (Ch. 32)
| Token | px | Use |
|---|---|---|
| `radius.none` | 0 | tables, full-bleed |
| `radius.small` | 4 | inputs, chips, badges |
| `radius.medium` | 8 | **default** — buttons, cards |
| `radius.large` | 12 | modals, large surfaces, workspace panels |
| `radius.full` | 999 | pills, avatars, toggles |

### Elevation (Ch. 31 — borders over shadows)
Elevation is intentionally minimal; **borders are the primary separators**, shadows only signal that something floats *above* the canvas.

| Token | Shadow | Level |
|---|---|---|
| `elevation.0` | none | Background / canvas |
| `elevation.1` | `0 1px 2px rgba(15,23,42,0.04)` + border | Surface / card |
| `elevation.2` | `0 4px 12px rgba(15,23,42,0.08)` | Overlay — dropdown, popover, drawer |
| `elevation.3` | `0 12px 32px rgba(15,23,42,0.12)` | Modal |
| `elevation.4` | `0 20px 48px rgba(15,23,42,0.16)` | Critical dialog |

### Motion (Ch. 34 — communicate, never entertain; never exceed 400ms)
| Token | Value | Use |
|---|---|---|
| `motion.duration.fast` | 120ms | hover, selection, feedback |
| `motion.duration.normal` | 200ms | drawers, panels, cards |
| `motion.duration.slow` | 320ms | workspace transitions |
| `motion.easing.standard` | `cubic-bezier(0.2, 0, 0.2, 1)` | most transitions |
| `motion.easing.entrance` | `cubic-bezier(0, 0, 0.2, 1)` | elements appearing |
| `motion.easing.exit` | `cubic-bezier(0.4, 0, 1, 1)` | elements leaving |

> **Reduced motion:** under `prefers-reduced-motion: reduce`, durations collapse toward 0 and transforms become opacity-only. AI panels must never animate in a way that traps focus (Ch. 37).

### Focus & borders
| Token | Value |
|---|---|
| `border.width.hairline` | 1px |
| `border.width.strong` | 2px |
| `focus.ring.width` | 2px |
| `focus.ring.offset` | 2px |
| `focus.ring.color` | `color.border.focus` (`#2563EB`) |

Focus is always visible (Ch. 37): a 2px ring in `border.focus` with a 2px offset, on every interactive element — never removed, only restyled.

### Z-index (layering, aligned to the 4-surface + elevation model)
| Token | Value | Layer |
|---|---|---|
| `z.base` | 0 | canvas / workspace |
| `z.sticky` | 100 | sticky headers, toolbars |
| `z.dropdown` | 1000 | menus, popovers |
| `z.overlay` | 1100 | drawers, side panels |
| `z.modal` | 1200 | modals |
| `z.toast` | 1300 | toasts / notifications |
| `z.critical` | 1400 | critical dialogs |

### Opacity
| Token | Value | Use |
|---|---|---|
| `opacity.disabled` | 0.4 | disabled controls |
| `opacity.scrim` | 0.45 | modal/overlay backdrop |

---

## 7. Theme architecture (Ch. 36)

Themes change **aliases only**. Primitives never change; components never change. Four themes ship:

### Dark
Canvas darkens; surfaces *lift toward* the light (they don't go pure black); semantic hues step **lighter** (400/500) so they stay legible on dark.

| Alias | Light | Dark |
|---|---|---|
| `color.canvas` | `#F8FAFC` | `#0A0F1A` |
| `color.bg.secondary` | `#F1F5F9` | `#0F1626` |
| `color.surface` | `#FFFFFF` | `#131C2E` |
| `color.surface.subtle` | `#F8FAFC` | `#0F1626` |
| `color.surface.hover` | `#F1F5F9` | `#1B2740` |
| `color.surface.selected` | `#EFF6FF` | `#16233F` |
| `color.text.primary` | `#0F172A` | `#F1F5F9` |
| `color.text.secondary` | `#475569` | `#94A3B8` |
| `color.text.tertiary` | `#64748B` | `#64748B` |
| `color.border.default` | `#E2E8F0` | `#24304A` |
| `color.border.strong` | `#CBD5E1` | `#33415C` |
| `color.border.focus` | `#2563EB` | `#60A5FA` |
| `color.primary` | `#2563EB` | `#3B82F6` |
| `color.primary.hover` | `#1D4ED8` | `#60A5FA` |
| `color.text.link` | `#1D4ED8` | `#93C5FD` |
| `success.text` | `#047857` | `#34D399` |
| `warning.text` | `#B45309` | `#FBBF24` |
| `danger.text` | `#B91C1C` | `#F87171` |
| `info.text` | `#1D4ED8` | `#60A5FA` |
| `color.ai.text` | `#6D28D9` | `#A78BFA` |
| `color.ai.subtle` | `#F5F3FF` | `#1E1B34` |
| `color.overlay.scrim` | `rgba(15,23,42,0.45)` | `rgba(2,6,23,0.65)` |

### High Contrast
For accessibility and low-vision directors. Text goes to pure `#000` / `#FFF`, borders become `border.width.strong` (2px) in `#000`, focus ring widens to 3px, and semantic hues use their darkest AA-max variants. Elevation shadows are dropped in favor of solid 2px borders. (Full alias table in [`tokens.css`](tokens.css) under `[data-theme="hc"]`.)

### Presentation Mode
For projecting board packs / running a live meeting on a shared screen. **Not a new palette** — it reuses Light, but:
- type scale steps **up one level** (body → body-lg, heading → page, etc.) via a `--ns-scale: 1.125` multiplier,
- density loosens (default gap `space.md`),
- muted/tertiary text is avoided; contrast raised toward High-Contrast.

Delivered as `[data-theme="presentation"]` reusing light aliases with the scale multiplier applied.

---

## 8. Accessibility guarantees baked into the tokens (Ch. 37)

- **Color independence:** every status has a `.text`/icon token *and* is always paired with a label or icon in components — color is never the only signal (green/amber/red are indistinguishable to many directors).
- **Contrast:** body and secondary text meet AA on their surfaces in every theme; the amber caution is documented (§2) so no component ships white-on-amber text.
- **Focus:** a visible 2px ring (3px in HC) on all interactive elements, never removed.
- **Zoom/scaling:** all type in rem; layouts reflow (Vol IV grid) rather than truncate.
- **Reduced motion:** honored via token collapse.
- **Touch targets:** minimum 44×44px hit area (enforced in component specs, Vol V) — a token `size.touch.min = 44px` is provided.

---

## 9. What I extended beyond the RFC (flag for review)

The RFC's Ch. 27 alias list was a *starter set*. To be buildable, I added the tokens real components need. These are **proposals**, not yet ratified:

1. **Interactive states** — `primary.hover` / `primary.pressed`, `surface.hover`, `surface.selected` (the RFC named none).
2. **Text depth** — added `text.tertiary` and `text.disabled` (RFC had primary/secondary/inverse only).
3. **Border depth** — added `border.subtle` and `border.strong` (RFC had default/focus only).
4. **Semantic sub-tokens** — split each status into `.fill / .subtle / .text / .on` so badges, buttons, and inline text all resolve correctly (this is what fixes the amber-contrast trap).
5. **AI tokens** — added `ai.border` and `ai.text` beyond the RFC's `ai.primary / ai.subtle`.
6. **Third font family** — added `font.family.reading` (serif, for long-form board papers) and `font.family.mono` (IDs/hashes/figures). RFC named only `font.family.primary`.
7. **Layering + focus + opacity + touch tokens** — z-index scale, focus-ring tokens, `opacity.disabled/scrim`, `size.touch.min`. Needed for real components; RFC didn't cover them.

**Open decisions for you:**
- **Typeface:** Inter is my recommendation (free, exceptional legibility, tabular figures). Alternatives if you want a distinct identity: *Geist*, *IBM Plex Sans*, or a licensed face. Reading serif (*Source Serif 4*) and mono (*JetBrains Mono*) are also swappable.
- **Primary hue:** I used a confident blue (`#2563EB`) per the RFC's "blue = navigation/primary." If CNI Group has a brand color, we retarget `color.primary` and the neutral tint to match — one token change.
- **Density default:** I set a comfortable default (16px body, `space.md` card padding). A "compact" density mode for data-heavy tables (audit log, registers) is worth adding in Vol V.

---

*Next (Vol V — Components): every component composes from these tokens — Button, Input, Badge, Card, Approval Card, Decision Timeline, Audit Log row, AI Insight panel, Workspace shell. No component introduces a new raw value.*
