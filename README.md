# design-dna

A Claude Code plugin that **learns a design system from the design work you already have**: creative briefs, magazines, portfolios, reports, brand guidelines, decks and moodboards. It ships the system to **Figma** (variables, styles, a Foundations page) and **Claude Design** (a design-system bundle with preview cards).

```
briefs · magazines · portfolios · reports · decks · images · saved web pages
        │  ingest: measure fonts, sizes, leading, palettes, margins, columns, whitespace,
        │          declared colors (hex/RGB/CMYK/Pantone), theme colors, font mentions
        ▼
   corpus/ ──► design-analyst agents look at every page render and write observations
        │          (mood, principles, hierarchy, imagery, shape, voice, brief locks)
        ▼  learn: weighted by role and weight, clustered in OKLab, consistency across sources
   profile.json  ◄── overrides.json (your decisions always win)
        ▼  generate
   DESIGN.md · tokens.css · DTCG tokens (light/dark) · preview.html
   figma/01-variables.js · 02-styles.js · 03-foundations.js  ──► Figma MCP (use_figma)
   claude-design/ (README, tokens, @dsCard previews)          ──► /design-sync → claude.ai/design
```

## Install

```bash
pip install -r scripts/requirements.txt
```

Then, in Claude Code:

```
/plugin marketplace add AK-1509/DesignDNA
/plugin install design-dna@design-dna
```

To install from a local clone, run `/plugin marketplace add <path-to-clone>` instead.

For local development, run `claude --plugin-dir ./design-dna` instead.

## Use

Just ask. For example:

> Learn our design language from `~/refs` (the brief is `brief.docx`, the rest are magazines and our portfolio), then build the design system and push it to Figma.

The four skills chain together:

| Skill | Does |
|---|---|
| `learn-design-corpus` | ingest files, run one `design-analyst` agent per source to review its page renders, then `learn` |
| `generate-design-system` | resolve decisions (overrides > brief locks > declared > learned > default), write tokens, docs and previews, check contrast |
| `export-to-figma` | run the three idempotent Plugin API scripts through the Figma MCP `use_figma` tool |
| `export-to-claude-design` | hand the bundle to `/design-sync`, an Artifact Design System type, or a manual upload |

The CLI also works on its own:

```bash
python scripts/dna.py init --name "Meridian"
python scripts/dna.py ingest refs/ --role magazine
python scripts/dna.py ingest refs/brief.md --role brief
python scripts/dna.py pending          # what still needs visual review
python scripts/dna.py learn
python scripts/dna.py generate
```

## How it learns

- **Evidence is weighted by role.** A brief's *declared* colors and fonts count heavily (×3), but the look of the brief document itself barely counts. Portfolios weigh most for visual evidence. You can give any source `--weight`.
- **Consistency beats volume.** Colors are clustered in OKLab across all sources. The primary is the accent with the best share × support (how many sources use it) × chroma score.
- **Typography comes from real text.** Display and body faces are the families carrying the most characters at headline and text sizes. The type scale ratio is fitted to the heading levels actually used and snapped to a standard ratio. Print leading and measure are converted for screen.
- **Layout is measured.** Margins, gutters, columns (from whitespace "rivers"), whitespace share and image coverage are measured on every sampled page.
- **Agents supply what scripts can't see.** The design-analyst agent reviews renders for mood, principles, hierarchy style, imagery, corner and elevation language, voice, and brief locks.
- **Every decision is cited.** DESIGN.md has a provenance table ("brief lock", "learned: top accent, 18% of color mass, in 80% of sources", "default…"). Defaults show exactly where the corpus was silent.
- **Nothing is overwritten silently.** Each `learn` snapshots the previous profile to `history/` and prints what changed.

## Outputs

See [`examples/meridian/`](examples/meridian/), which was generated from the synthetic corpus in `tests/`:

- `DESIGN.md`: essence, principles, semantic tokens with light/dark values, palette, a WCAG contrast table, type scale, layout, component recipes, do/don't, and provenance
- `tokens.css` and `tokens/*.tokens.json`: W3C DTCG (legacy string values by default, `--format 2025` for spec-2025 objects)
- `figma/`: collections Primitives / Color (Light, Dark) / Typography / Spacing with scopes and code syntax, text and effect styles, and a Foundations page
- `claude-design/`: README + tokens + `preview/*.html` cards with `@dsCard` markers
- `preview.html`: a live specimen with a theme toggle

## Test

```bash
python tests/smoke_test.py
```

This builds a synthetic corpus (a two-column magazine, a report, a portfolio PNG, a markdown brief and a .pptx theme). It runs the whole pipeline, asserts on the extraction, learning and generation results, and syntax-checks the Figma scripts with Node if Node is installed.

## Limits

- Scanned PDFs have no text layer, so only color, layout and visual review apply. OCR them first if type matters.
- .pptx gives theme colors and fonts plus embedded images. Export decks to PDF for full analysis.
- Proprietary brand fonts are kept as the brand face, with a Google Fonts substitute for web and Figma.
- Figma plans with a one-mode limit will skip the Dark mode (a warning is reported, and the dark tokens remain in DTCG).
