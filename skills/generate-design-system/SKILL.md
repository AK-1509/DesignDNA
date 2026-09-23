---
name: generate-design-system
description: Turn a learned design-dna profile into a complete design system. Outputs are DTCG design tokens (light/dark), CSS variables and type classes, a DESIGN.md guide with provenance and contrast checks, a live HTML specimen, Figma variable/style scripts and a Claude Design bundle. Use it after learn-design-corpus, when the user asks to generate, regenerate, tweak or override the design system (e.g. "make the primary darker", "use Inter for body", "rounder corners").
argument-hint: "[--name \"System name\"]"
---

# Generate the design system

```
DNA = python "${CLAUDE_PLUGIN_ROOT}/scripts/dna.py"
```

If `${CLAUDE_PLUGIN_ROOT}` is not expanded, use `<this skill's base dir>/../../scripts/dna.py`.

## Workflow

1. **Check freshness**: `$DNA status`. If it says the corpus changed since the last profile, run `$DNA learn` first. If there's no corpus, switch to the `learn-design-corpus` skill.

2. **Settle decisions before generating.** Read `.design-dna/profile.md`. If anything important is low-confidence or conflicting (for example two briefs name different primaries, or no display face was found), ask the user **one** focused question, or proceed with the learned value and say so. Record explicit decisions in `.design-dna/overrides.json`; anything set there wins over learning:

   ```json
   {
     "name": "Meridian",
     "color": {"primary": "#E4572E", "accent": null, "neutral": null, "background": "#F6F1E7", "text": null},
     "typography": {"display": "Playfair Display", "body": "Source Serif 4", "mono": null, "ratio": 1.333, "base_px": 18},
     "shape": {"corners": "sharp|subtle|soft|round|pill", "elevation": "flat|subtle|layered", "borders": "none|hairline|bold"},
     "density": "airy|balanced|dense"
   }
   ```
   Null or missing keys fall back to learning. Edit this file (not the generated outputs) when the user asks for a change, then regenerate.

3. **Generate**: `$DNA generate [--name "…"] [--format legacy|2025]`. `legacy` writes DTCG values as strings (`"#E4572E"`, `"16px"`), which most tools read today. `2025` writes the object values from the DTCG 2025.10 spec. Output goes to `.design-dna/output/<slug>/`:

   | Path | Use |
   |---|---|
   | `DESIGN.md` | the system guide: essence, principles, tokens, contrast, components, provenance |
   | `preview.html` | a visual specimen (light/dark toggle) |
   | `tokens.css` | CSS custom properties, semantic light/dark, `.text-*` classes |
   | `tokens/*.tokens.json` | DTCG: primitives, color.light, color.dark, typography, plus combined `tokens.json` |
   | `figma/` | `variables.json` spec and three `use_figma` scripts (see `export-to-figma`) |
   | `claude-design/` | README, tokens and `@dsCard` preview cards (see `export-to-claude-design`) |
   | `system.json` | every resolved decision, machine-readable |

4. **Review before presenting.** Read `DESIGN.md` and check:
   - **Contrast table.** Every row should pass. The generator already shifts action colors and link steps for AA. If something is still ⚠️, fix it with an override and say what changed.
   - **Provenance.** Every major decision should trace to an override, a brief lock, a declared value or learned evidence. Call out anything that fell to a *default*, because that's where the corpus was silent.
   - **Fonts.** If the brand face is proprietary (for example Neue Haas Grotesk), the system uses it with a Google Fonts substitute for web and Figma. Tell the user which substitute was chosen.

5. **Show it.** Open `preview.html` in the browser preview if one is available, or publish it as an artifact when the user wants a shareable page. Give a short summary: the name, the primary/accent/paper colors, the type pairing and scale, the density and corner style, and the 3 strongest principles.

6. **Offer the exports**: Figma (`export-to-figma`) and Claude Design (`export-to-claude-design`).

## How decisions are made (for explaining to the user)

- **Color**: the primary is the highest-scoring accent cluster, scored by share of color mass × consistency across sources × chroma. Brief-declared or locked colors take precedence. The accent is a second hue at least 30° away, or a derived split-complement. Neutrals are tinted with the corpus's average neutral hue. Ramps are OKLCH, and the brand color sits *exactly* on its nearest step.
- **Type**: the display and body faces are the families that carry the most characters at headline and text sizes. The scale ratio comes from fitting a geometric progression to real heading levels, snapped to a standard ratio. Leading and measure come from print, converted for screen.
- **Layout**: margins, gutters, columns, whitespace and image coverage are measured from page geometry. Density comes from whitespace, or from the visual-review consensus when there is one.
- **Shape, motion and voice** come from the design-analyst observations, falling back to inference from mood.
