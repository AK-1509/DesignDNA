# Meridian — Design System

> Distilled by **design-dna** from 5 sources (1 brief, 1 portfolio, 1 reference, 1 report, 1 magazine). Profile learned 2026-09-23T17:09:55Z.

This file is the source of truth for anyone (human or model) designing with this system. Use the tokens in `tokens.css` / `tokens/*.json`; never hard-code values that have a token.

## Essence

**Mood:** warm, confident, editorial, restrained

> Rebrand brief for an essay publisher. _(from a brief)_

> A restrained editorial magazine on warm paper. _(from a magazine)_

### Principles

1. Make long reading comfortable on screen _(seen in 1 source)_
2. Wide margins frame every spread _(seen in 1 source)_
3. One accent color per spread _(seen in 1 source)_
4. Let the canvas breathe: on average 55% of each page is left empty. _(measured)_
5. Color is structural, not decorative: ~44% of the corpus is chromatic. _(measured)_
6. Typography does the heavy lifting; imagery is occasional. _(measured)_
7. Hold body text to a ~68-character measure. _(measured)_

### From the brief

- **Project:** Meridian Press rebrand
- **Audience:** curious readers 25-55
- **Goal:** Feel editorial and confident

### Voice

**Attributes:** precise, wry, warm


## Color

Primary is **orange-red** `#E4572E` (brief lock). Accent is **dark blue** `#1D3557` (declared as accent/secondary in hex, theme). The canvas is **warm off-white** `#F6F1E7`. Text is **near-black ink** `#1A1A1A`.

Chromatic color covers about **44%** of the corpus. Match that proportion. Color is structural here, so large fields of primary or accent are on-brand. Keep text on neutrals.

### Semantic tokens

| Token | CSS variable | Light | Dark |
|---|---|---|---|
| `bg.canvas` | `--color-bg-canvas` | `#F6F1E7` ← base.paper | `#0F0E0C` ← neutral.950 |
| `bg.surface` | `--color-bg-surface` | `#FFFFFF` ← base.surface | `#1D1C17` ← neutral.900 |
| `bg.subtle` | `--color-bg-subtle` | `#F5F2EC` ← neutral.100 | `#302E29` ← neutral.800 |
| `bg.muted` | `--color-bg-muted` | `#E6E4DD` ← neutral.200 | `#4A4842` ← neutral.700 |
| `bg.inverse` | `--color-bg-inverse` | `#1D1C17` ← neutral.900 | `#FBFAF6` ← neutral.50 |
| `text.default` | `--color-text-default` | `#1A1A1A` ← base.ink | `#F6F1E7` ← base.paper |
| `text.muted` | `--color-text-muted` | `#605D58` ← neutral.600 | `#D3D1CA` ← neutral.300 |
| `text.subtle` | `--color-text-subtle` | `#7C7A74` ← neutral.500 | `#A7A49E` ← neutral.400 |
| `text.inverse` | `--color-text-inverse` | `#FBFAF6` ← neutral.50 | `#1D1C17` ← neutral.900 |
| `text.link` | `--color-text-link` | `#C03908` ← brand.600 | `#FFA78F` ← brand.300 |
| `border.default` | `--color-border-default` | `#E6E4DD` ← neutral.200 | `#302E29` ← neutral.800 |
| `border.strong` | `--color-border-strong` | `#A7A49E` ← neutral.400 | `#605D58` ← neutral.600 |
| `border.focus` | `--color-border-focus` | `#E4572E` ← brand.500 | `#FF754F` ← brand.400 |
| `primary.default` | `--color-primary-default` | `#E4572E` ← brand.500 | `#E4572E` ← brand.500 |
| `primary.hover` | `--color-primary-hover` | `#C03908` ← brand.600 | `#FF754F` ← brand.400 |
| `primary.subtle` | `--color-primary-subtle` | `#FFE7E0` ← brand.100 | `#561200` ← brand.900 |
| `primary.on` | `--color-primary-on` | `#0F0E0C` ← neutral.950 | `#0F0E0C` ← neutral.950 |
| `accent.default` | `--color-accent-default` | `#1D3557` ← accent.900 | `#91A6C5` ← accent.400 |
| `accent.hover` | `--color-accent-hover` | `#091A33` ← accent.950 | `#B0C2DC` ← accent.300 |
| `accent.subtle` | `--color-accent-subtle` | `#E3EEFE` ← accent.100 | `#1D3557` ← accent.900 |
| `accent.on` | `--color-accent-on` | `#FFFFFF` ← base.white | `#0F0E0C` ← neutral.950 |
| `success.default` | `--color-success-default` | `#457F3D` ← success.600 | `#7BB673` ← success.400 |
| `success.subtle` | `--color-success-subtle` | `#D9F7D5` ← success.100 | `#12370D` ← success.900 |
| `success.text` | `--color-success-text` | `#31672A` ← success.700 | `#C0E8BA` ← success.200 |
| `warning.default` | `--color-warning-default` | `#906603` ← warning.600 | `#D3A249` ← warning.400 |
| `warning.subtle` | `--color-warning-subtle` | `#FFEAC8` ← warning.100 | `#3E2A00` ← warning.900 |
| `warning.text` | `--color-warning-text` | `#745100` ← warning.700 | `#FBD596` ← warning.200 |
| `danger.default` | `--color-danger-default` | `#CB473F` ← danger.600 | `#F67A6E` ← danger.400 |
| `danger.subtle` | `--color-danger-subtle` | `#FFE6E3` ← danger.100 | `#5D0004` ← danger.900 |
| `danger.text` | `--color-danger-text` | `#9E2220` ← danger.700 | `#FFCDC6` ← danger.200 |
| `info.default` | `--color-info-default` | `#0071C3` ← info.600 | `#50AAFF` ← info.400 |
| `info.subtle` | `--color-info-subtle` | `#E0EFFF` ← info.100 | `#002F56` ← info.900 |
| `info.text` | `--color-info-text` | `#005A9D` ← info.700 | `#C0DEFF` ← info.200 |

### Palette (primitives)

| Ramp | 50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900 | 950 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| brand | `#FFF4F1` | `#FFE7E0` | `#FFCEC0` | `#FFA78F` | `#FF754F` | **`#E4572E`** | `#C03908` | `#9C2A00` | `#781E00` | `#561200` | `#360800` |
| accent | `#F2F7FF` | `#E3EEFE` | `#CEDCF1` | `#B0C2DC` | `#91A6C5` | `#738BAC` | `#577093` | `#40597D` | `#2A4366` | **`#1D3557`** | `#091A33` |
| neutral | `#FBFAF6` | `#F5F2EC` | `#E6E4DD` | `#D3D1CA` | `#A7A49E` | `#7C7A74` | `#605D58` | `#4A4842` | `#302E29` | `#1D1C17` | `#0F0E0C` |
| success | `#E8FEE5` | `#D9F7D5` | `#C0E8BA` | `#9ED196` | `#7BB673` | **`#5E9B56`** | `#457F3D` | `#31672A` | `#204F1A` | `#12370D` | `#072105` |
| warning | `#FFF6E6` | `#FFEAC8` | `#FBD596` | `#E8B967` | **`#D3A249`** | `#AE8024` | `#906603` | `#745100` | `#583D00` | `#3E2A00` | `#261800` |
| danger | `#FFF4F2` | `#FFE6E3` | `#FFCDC6` | `#FFA69B` | `#F67A6E` | `#DC584E` | **`#CB473F`** | `#9E2220` | `#7E0D0F` | `#5D0004` | `#3B0001` |
| info | `#F1F8FF` | `#E0EFFF` | `#C0DEFF` | `#8FC6FF` | `#50AAFF` | **`#0083E0`** | `#0071C3` | `#005A9D` | `#004478` | `#002F56` | `#001B36` |

Bold values are anchors: the exact colors found in the corpus.

### Contrast

| Mode | Pair | Ratio | Target | |
|---|---|---|---|---|
| light | `text.default` on `bg.canvas` | 15.46:1 | 7.0:1 | ✅ |
| light | `text.default` on `bg.surface` | 17.4:1 | 7.0:1 | ✅ |
| light | `text.muted` on `bg.canvas` | 5.82:1 | 4.5:1 | ✅ |
| light | `text.subtle` on `bg.canvas` | 3.81:1 | 3.0:1 | ✅ |
| light | `text.link` on `bg.canvas` | 4.87:1 | 4.5:1 | ✅ |
| light | `primary.on` on `primary.default` | 5.24:1 | 4.5:1 | ✅ |
| light | `accent.on` on `accent.default` | 12.36:1 | 4.5:1 | ✅ |
| light | `success.text` on `success.subtle` | 5.87:1 | 4.5:1 | ✅ |
| light | `warning.text` on `warning.subtle` | 6.12:1 | 4.5:1 | ✅ |
| light | `danger.text` on `danger.subtle` | 6.54:1 | 4.5:1 | ✅ |
| light | `info.text` on `info.subtle` | 6.09:1 | 4.5:1 | ✅ |
| dark | `text.default` on `bg.canvas` | 17.14:1 | 7.0:1 | ✅ |
| dark | `text.default` on `bg.surface` | 15.16:1 | 7.0:1 | ✅ |
| dark | `text.muted` on `bg.canvas` | 12.63:1 | 4.5:1 | ✅ |
| dark | `text.subtle` on `bg.canvas` | 7.76:1 | 3.0:1 | ✅ |
| dark | `text.link` on `bg.canvas` | 10.27:1 | 4.5:1 | ✅ |
| dark | `primary.on` on `primary.default` | 5.24:1 | 4.5:1 | ✅ |
| dark | `accent.on` on `accent.default` | 7.78:1 | 4.5:1 | ✅ |
| dark | `success.text` on `success.subtle` | 9.82:1 | 4.5:1 | ✅ |
| dark | `warning.text` on `warning.subtle` | 9.8:1 | 4.5:1 | ✅ |
| dark | `danger.text` on `danger.subtle` | 10.09:1 | 4.5:1 | ✅ |
| dark | `info.text` on `info.subtle` | 9.82:1 | 4.5:1 | ✅ |

## Typography

| Role | Brand face | Web / Figma face | Category | Why |
|---|---|---|---|---|
| display | Playfair Display | Playfair Display | serif | brief lock |
| body | Source Serif 4 | Source Serif 4 | serif | brief lock |
| mono | JetBrains Mono | JetBrains Mono | mono | default |

If the brand face is licensed, load it and keep the web face as the fallback. Otherwise use the web face, which is on Google Fonts and in Figma.

**Scale:** base 18px × 1.618 (learned: heading levels [2.449] fit 2.449 → golden ratio).  
**Line height:** body 1.65, heading 1.35, display 1.1.  
**Measure:** 68ch.

| Style | Class | Face | Size | Weight | Line height | Tracking | Case |
|---|---|---|---|---|---|---|---|
| display-xl | `.text-display-xl` | display | 123px | 700 | 1.1 | -0.01em | — |
| display-lg | `.text-display-lg` | display | 76px | 700 | 1.1 | -0.01em | — |
| heading-1 | `.text-heading-1` | display | 47px | 700 | 1.35 | 0em | — |
| heading-2 | `.text-heading-2` | display | 37px | 700 | 1.35 | 0em | — |
| heading-3 | `.text-heading-3` | display | 29px | 600 | 1.35 | 0em | — |
| body-lg | `.text-body-lg` | body | 29px | 400 | 1.65 | 0em | — |
| body | `.text-body` | body | 18px | 400 | 1.65 | 0em | — |
| body-sm | `.text-body-sm` | body | 13px | 400 | 1.65 | 0em | — |
| label | `.text-label` | body | 13px | 600 | 1.35 | 0.08em | UPPER |
| caption | `.text-caption` | body | 11px | 400 | 1.35 | 0em | — |
| quote | `.text-quote` | display | 47px | 400 | 1.35 | 0em | — italic |
| code | `.text-code` | mono | 13px | 400 | 1.65 | 0em | — |

Typefaces named in the corpus text: Playfair Display, Source Serif 4.

## Layout & spacing

- **Density:** airy (visual review consensus)
- **Grid:** 12 columns, 44px gutters, 1200px max width. Page margin is 120px on desktop and 24px on mobile (learned: print margins ≈ 8.2% of page width)
- **Rhythm:** 32px between blocks, 128px between sections
- **Measure:** 68ch for running text (learned: ~62 chars per body line in print)
- The print corpus mostly uses **2 columns**. Echo that on wide screens for editorial layouts.
- **Imagery:** type-led (images cover 8% of page area)

Spacing scale (4px base): `space-0`=0px, `space-0-5`=2px, `space-1`=4px, `space-1-5`=6px, `space-2`=8px, `space-3`=12px, `space-4`=16px, `space-5`=20px, `space-6`=24px, `space-8`=32px, `space-10`=40px, `space-12`=48px, `space-16`=64px, `space-20`=80px, `space-24`=96px, `space-32`=128px

- two-column text grid

## Shape & elevation

- **Corners:** sharp (visual review consensus): `radius-none`=0, `radius-sm`=0, `radius-md`=0, `radius-lg`=2, `radius-xl`=4, `radius-full`=full, `radius-control`=0
- **Borders:** hairline. Widths: hairline=1px, default=1px, strong=2px
- **Elevation:** flat (visual review consensus). Prefer borders and tone shifts to shadows.
- **Motion:** 144/240/384ms, standard easing `cubic-bezier(0.2, 0, 0, 1)`. Respect `prefers-reduced-motion`.

## Components

Build every component from semantic tokens. These are the recipes:

| Component | Recipe |
|---|---|
| Button (primary) | bg `primary.default`, text `primary.on`, hover `primary.hover`, radius `control`, padding `space-2`/`space-4`, `body` semibold, focus ring 2px `border.focus` offset 2px |
| Button (secondary) | transparent bg, 1px `border.strong`, text `text.default`; hover bg `bg.subtle` |
| Link | `text.link`, underline offset 0.2em; hover darkens one step |
| Input | bg `bg.surface`, 1px `border.strong`, radius `md`, `body` text, label `label` style in `text.muted`; focus `border.focus` |
| Card | bg `bg.surface`, 1px `border.default`, radius `lg`, no shadow |
| Badge / tag | bg `{status}.subtle` or `primary.subtle`, text `{status}.text`, `label` style, radius `full` or `sm` |
| Alert | bg `{status}.subtle`, 3px left border `{status}.default`, text `{status}.text` |
| Article | column max `measure`, kicker `label`, title `heading-1`, body `body` with `stack-gap` paragraphs, pull quote `quote` with 3px `accent.default` rule |
| Data table | `body-sm`, header `label` on `bg.subtle`, hairline `border.default` rows, numbers tabular-nums right-aligned |

Patterns observed in the corpus: pull quote (×1), kicker (×1), caption (×1).

## Do

- Run photographs full bleed
- Pair Playfair Display (display) with Source Serif 4 (text). Don't swap their roles.

## Don't

- No drop shadows
- Don't introduce new hues. The palette is orange-red + dark blue + tinted neutrals.

## Provenance

| Decision | Source |
|---|---|
| color.primary | brief lock |
| color.accent | declared as accent/secondary in hex, theme |
| color.neutral | learned neutral tint (hue 90°, chroma 0.009) |
| color.paper | brief lock |
| color.ink | learned ink color (near-black ink) |
| color.status | success: learned (green #5E9B56); warning: learned (yellow #D3A249); danger: generated, chroma matched to primary; info: generated, chroma matched to primary |
| color.primary.light | step 500 (anchor); text on it is near-black at 5.2:1 (white would be 3.7:1) |
| color.accent.light | step 900 (anchor); text on it is white at 12.4:1 |
| color.primary.dark | step 500 (anchor); text on it is near-black at 5.2:1 (white would be 3.7:1) |
| color.accent.dark | step 400 (anchor 900 shifted for AA); text on it is near-black at 7.8:1 (white would be 2.5:1) |
| font.display | brief lock |
| font.body | brief lock |
| font.mono | default |
| font.scale | learned: heading levels [2.449] fit 2.449 → golden ratio |
| font.base | serif text face reads best at 18px on screen |
| layout.density | visual review consensus |
| layout.margin | learned: print margins ≈ 8.2% of page width |
| layout.measure | learned: ~62 chars per body line in print |
| shape.corners | visual review consensus |
| shape.elevation | visual review consensus |
| shape.borders | visual review consensus |

Confidence: color 90%, typography 75%, layout 75%, qualitative 40%

## Files

- `tokens.css`: CSS custom properties, light/dark semantics, `.text-*` style classes
- `tokens/*.tokens.json`: W3C DTCG tokens (primitives, color.light, color.dark, typography); `tokens/tokens.json` combines them
- `figma/variables.json` + `figma/0*.js`: Figma variables, styles and a Foundations page (run via the Figma MCP)
- `preview.html`: visual specimen of the whole system
- `claude-design/`: bundle for a claude.ai/design design-system project (this README, tokens, `index.html`, and `preview/*.html` cards tagged with `@dsCard` groups)
