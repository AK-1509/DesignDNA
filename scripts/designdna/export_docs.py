"""Human- and model-readable outputs: DESIGN.md (also the Claude Design README) and preview.html."""
from __future__ import annotations

import html
import re
from urllib.parse import quote_plus

from . import color as C
from .export_tokens import css as tokens_css

SINGLE_WEIGHT = {"Anton", "Bebas Neue", "Abril Fatface", "DM Serif Display", "Instrument Serif", "Michroma"}


def _pct(v):
    return "—" if v is None else f"{v:.0%}"


def design_md(s: dict) -> str:
    col, ty, lay, shape, g = s["color"], s["typography"], s["layout"], s["shape"], s["guidance"]
    fam = ty["families"]
    corpus = s.get("corpus", {})
    roles = ", ".join(f"{v} {k}{'s' if v != 1 else ''}" for k, v in (corpus.get("roles") or {}).items())
    L = [f"# {s['name']} — Design System", "",
         f"> Distilled by **design-dna** from {corpus.get('sources', 0)} sources ({roles}). "
         f"Profile learned {s.get('generated_at') or ''}.", "",
         "This file is the source of truth for anyone (human or model) designing with this system. "
         "Use the tokens in `tokens.css` / `tokens/*.json`; never hard-code values that have a token.", ""]

    L += ["## Essence", ""]
    if g["mood"]:
        L += [f"**Mood:** {', '.join(g['mood'][:8])}", ""]
    for sm in g["summaries"][:3]:
        L += [f"> {sm['summary']} _(from a {sm['role']})_", ""]
    L += ["### Principles", ""]
    L += [f"{i}. {p['text']}" + (f" _(seen in {p['sources']} source{'s' if p['sources'] != 1 else ''})_"
                                  if p.get("sources") else " _(measured)_")
          for i, p in enumerate(g["principles"][:12], 1)]
    L.append("")
    if g["briefs"]:
        L += ["### From the brief", ""]
        for b in g["briefs"][:3]:
            if b.get("project"):
                L.append(f"- **Project:** {b['project']}")
            if b.get("audience"):
                L.append(f"- **Audience:** {b['audience']}")
            for goal in (b.get("goals") or [])[:5]:
                L.append(f"- **Goal:** {goal}")
            for c in (b.get("constraints") or [])[:5]:
                L.append(f"- **Constraint:** {c}")
        L.append("")
    if g["voice"]:
        L += ["### Voice", "", f"**Attributes:** {', '.join(g['voice'][:6])}", ""]
        L += [f"- “{p}”" for p in g["phrases"][:4]]
        L.append("")

    L += ["## Color", "",
          f"Primary is **{col['names']['primary']}** `{col['primary']}` ({s['provenance'].get('color.primary', '')}). "
          f"Accent is **{col['names']['accent']}** `{col['accent']}` ({s['provenance'].get('color.accent', '')}). "
          f"The canvas is **{col['names']['paper']}** `{col['base']['paper']}`. Text is **{col['names']['ink']}** `{col['base']['ink']}`.", ""]
    cov = col.get("accent_coverage")
    if cov is not None:
        advice = ("Neutrals do the structural work, and primary marks action and emphasis." if cov < 0.15 else
                  "Color is structural here, so large fields of primary or accent are on-brand. Keep text on neutrals."
                  if cov >= 0.3 else "Use color for emphasis and for a few full-bleed moments. Neutrals carry the rest.")
        L += [f"Chromatic color covers about **{cov:.0%}** of the corpus. Match that proportion. {advice}", ""]
    L += ["### Semantic tokens", "", "| Token | CSS variable | Light | Dark |", "|---|---|---|---|"]
    lv, dv = col["values"]["light"], col["values"]["dark"]
    for name, ref in col["semantic"]["light"].items():
        L.append(f"| `{name}` | `--color-{name.replace('.', '-')}` | `{lv[name]}` ← {ref} | `{dv[name]}` ← {col['semantic']['dark'][name]} |")
    L += ["", "### Palette (primitives)", "", "| Ramp | " + " | ".join(str(x) for x in C.STEPS) + " |",
          "|---|" + "---|" * len(C.STEPS)]
    for group, ramp in col["ramps"].items():
        anchor = col["anchors"].get(group)
        L.append(f"| {group} | " + " | ".join(f"**`{ramp[st]}`**" if st == anchor else f"`{ramp[st]}`" for st in C.STEPS) + " |")
    L += ["", "Bold values are anchors: the exact colors found in the corpus.", "",
          "### Contrast", "", "| Mode | Pair | Ratio | Target | |", "|---|---|---|---|---|"]
    for r in col["contrast"]:
        L.append(f"| {r['mode']} | `{r['fg']}` on `{r['bg']}` | {r['ratio']}:1 | {r['target']}:1 | {'✅' if r['pass'] else '⚠️'} |")
    if g["color_notes"]:
        L += ["", "Observed in the corpus:", ""] + [f"- {n}" for n in g["color_notes"]]
    L.append("")

    L += ["## Typography", "", "| Role | Brand face | Web / Figma face | Category | Why |", "|---|---|---|---|---|"]
    for role in ("display", "body", "mono"):
        f = fam[role]
        L.append(f"| {role} | {f['name']} | {f['web']} | {f['category']} | {s['provenance'].get('font.' + role, '')} |")
    L += ["", f"If the brand face is licensed, load it and keep the web face as the fallback. Otherwise use the web face, which is on Google Fonts and in Figma.", "",
          f"**Scale:** base {ty['base']}px × {ty['ratio']} ({s['provenance'].get('font.scale', '')}).  ",
          f"**Line height:** body {ty['line_height']['body']}, heading {ty['line_height']['heading']}, "
          f"display {ty['line_height']['display']}.  ",
          f"**Measure:** {lay['measure']}ch.", "",
          "| Style | Class | Face | Size | Weight | Line height | Tracking | Case |", "|---|---|---|---|---|---|---|---|"]
    for st in ty["styles"]:
        L.append(f"| {st['name']} | `.text-{st['name']}` | {st['family']} | {st['px']}px | {st['weight_value']} | "
                 f"{st['lh_value']} | {st['ls_value']:g}em | {'UPPER' if st['case'] == 'UPPER' else '—'}"
                 f"{' italic' if st['italic'] else ''} |")
    if ty["declared"]:
        L += ["", "Typefaces named in the corpus text: " + ", ".join(d["family"] for d in ty["declared"][:6]) + "."]
    if g["typography_notes"]:
        L += ["", "Observed in the corpus:", ""] + [f"- {n}" for n in g["typography_notes"]]
    L.append("")

    L += ["## Layout & spacing", "",
          f"- **Density:** {lay['density']} ({s['provenance'].get('layout.density', '')})",
          f"- **Grid:** {lay['columns']} columns, {lay['gutter']}px gutters, {lay['max_width']}px max width. "
          f"Page margin is {lay['margin']}px on desktop and {lay['margin_mobile']}px on mobile ({s['provenance'].get('layout.margin', '')})",
          f"- **Rhythm:** {lay['stack_gap']}px between blocks, {lay['section_gap']}px between sections",
          f"- **Measure:** {lay['measure']}ch for running text ({s['provenance'].get('layout.measure', '')})"]
    if lay.get("print_columns"):
        L.append(f"- The print corpus mostly uses **{lay['print_columns']} columns**. Echo that on wide screens for editorial layouts.")
    if lay.get("imagery"):
        L.append(f"- **Imagery:** {lay['imagery']} (images cover {_pct(lay.get('image_coverage'))} of page area)")
    L += ["", "Spacing scale (4px base): " + ", ".join(f"`space-{k}`={v}px" for k, v in s["space"].items()), ""]
    for n in g["composition"]:
        L.append(f"- {n}")

    L += ["", "## Shape & elevation", "",
          f"- **Corners:** {shape['corners']} ({s['provenance'].get('shape.corners', '')}): "
          + ", ".join(f"`radius-{k}`={v if v < 9999 else 'full'}" for k, v in shape["radius"].items()),
          f"- **Borders:** {shape['borders']}. Widths: " + ", ".join(f"{k}={v}px" for k, v in shape["border_width"].items()),
          f"- **Elevation:** {shape['elevation']} ({s['provenance'].get('shape.elevation', '')})."
          + (" Prefer borders and tone shifts to shadows." if shape["elevation"] == "flat" else ""),
          f"- **Motion:** {s['motion']['duration']['fast']}/{s['motion']['duration']['base']}/{s['motion']['duration']['slow']}ms, "
          "standard easing `cubic-bezier(0.2, 0, 0, 1)`. Respect `prefers-reduced-motion`.", ""]

    if g["imagery"]:
        L += ["## Imagery", ""]
        for im in g["imagery"]:
            L.append("- " + "; ".join(f"{k}: {v}" for k, v in im.items() if k != "source" and isinstance(v, (str, int, float))))
        L.append("")

    L += ["## Components", "", "Build every component from semantic tokens. These are the recipes:", "",
          "| Component | Recipe |", "|---|---|",
          "| Button (primary) | bg `primary.default`, text `primary.on`, hover `primary.hover`, radius `control`, padding `space-2`/`space-4`, `body` semibold, focus ring 2px `border.focus` offset 2px |",
          "| Button (secondary) | transparent bg, 1px `border.strong`, text `text.default`; hover bg `bg.subtle` |",
          "| Link | `text.link`, underline offset 0.2em; hover darkens one step |",
          "| Input | bg `bg.surface`, 1px `border.strong`, radius `md`, `body` text, label `label` style in `text.muted`; focus `border.focus` |",
          f"| Card | bg `bg.surface`, 1px `border.default`, radius `lg`, {'no shadow' if shape['elevation'] == 'flat' else 'shadow `sm`, `md` on hover'} |",
          "| Badge / tag | bg `{status}.subtle` or `primary.subtle`, text `{status}.text`, `label` style, radius `full` or `sm` |",
          "| Alert | bg `{status}.subtle`, 3px left border `{status}.default`, text `{status}.text` |",
          "| Article | column max `measure`, kicker `label`, title `heading-1`, body `body` with `stack-gap` paragraphs, pull quote `quote` with 3px `accent.default` rule |",
          "| Data table | `body-sm`, header `label` on `bg.subtle`, hairline `border.default` rows, numbers tabular-nums right-aligned |", ""]
    if g["components_seen"]:
        L += ["Patterns observed in the corpus: " + ", ".join(f"{k} (×{v})" for k, v in list(g["components_seen"].items())[:14]) + ".", ""]

    L += ["## Do", ""] + [f"- {d}" for d in g["dos"]] + ["", "## Don't", ""] + [f"- {d}" for d in g["donts"]] + [""]

    L += ["## Provenance", "", "| Decision | Source |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in s["provenance"].items()]
    conf = s.get("confidence") or {}
    if conf:
        L += ["", "Confidence: " + ", ".join(f"{k} {_pct(v)}" for k, v in conf.items())]
    if s.get("lock_conflicts"):
        L += ["", f"⚠️ Briefs disagree on: {', '.join(c['lock'] for c in s['lock_conflicts'])}. Resolve these in overrides.json."]
    L += ["", "## Files", "",
          "- `tokens.css`: CSS custom properties, light/dark semantics, `.text-*` style classes",
          "- `tokens/*.tokens.json`: W3C DTCG tokens (primitives, color.light, color.dark, typography); `tokens/tokens.json` combines them",
          "- `figma/variables.json` + `figma/0*.js`: Figma variables, styles and a Foundations page (run via the Figma MCP)",
          "- `preview.html`: visual specimen of the whole system",
          "- `claude-design/`: bundle for a claude.ai/design design-system project (this README, tokens, `index.html`, "
          "and `preview/*.html` cards tagged with `@dsCard` groups)", ""]
    return "\n".join(L)


# ---------------------------------------------------------------------------
# preview.html
# ---------------------------------------------------------------------------

def _font_links(s: dict) -> str:
    fam = s["typography"]["families"]
    need: dict[str, set] = {}
    for role, f in fam.items():
        weights = need.setdefault(f["web"], set())
        if role == "display":
            weights.update({s["typography"]["weights"]["display"], 400})
        elif role == "body":
            weights.update({s["typography"]["weights"]["regular"], 600, 700})
        else:
            weights.add(400)
    links = ['<link rel="preconnect" href="https://fonts.googleapis.com">',
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>']
    for name, weights in need.items():
        q = quote_plus(name)
        spec = "" if name in SINGLE_WEIGHT else ":wght@" + ";".join(str(w) for w in sorted(weights))
        links.append(f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={q}{spec}&display=swap">')
    return "\n".join(links)


PAGE_CSS = """
*, *::before, *::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--color-bg-canvas); color: var(--color-text-default); font-family: var(--font-body);
  font-size: var(--text-base); line-height: var(--leading-body); -webkit-font-smoothing: antialiased; }
.wrap { max-width: var(--layout-max-width); margin: 0 auto; padding: 0 16px; }
@media (min-width: 768px) { .wrap { padding: 0 clamp(24px, 5vw, var(--layout-margin)); } }
h1, h2, h3, p, ol, ul, figure, blockquote { margin: 0; }
h1, h2, h3 { overflow-wrap: anywhere; }
.topbar { position: sticky; top: 0; z-index: 5; background: var(--color-bg-canvas); border-bottom: var(--border-width-hairline) solid var(--color-border-default); }
.topbar .wrap { display: flex; align-items: center; justify-content: space-between; gap: 16px; min-height: 56px; }
.topbar nav { display: flex; gap: 16px; overflow-x: auto; scrollbar-width: none; }
.topbar nav a { color: var(--color-text-muted); text-decoration: none; white-space: nowrap; }
.topbar nav a:hover { color: var(--color-text-default); }
section { padding-block: calc(var(--layout-section-gap) * 0.6); border-bottom: var(--border-width-hairline) solid var(--color-border-default); }
section > * + * { margin-top: var(--layout-stack-gap); }
.kicker { color: var(--color-text-muted); }
.muted { color: var(--color-text-muted); }
.hero { padding-block: calc(var(--layout-section-gap) * 0.8); }
.hero .text-display-xl { max-width: 14ch; }
.lede { max-width: var(--layout-measure); color: var(--color-text-muted); }
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip { font-size: var(--text-sm); padding: 2px 10px; border-radius: var(--radius-full); background: var(--color-bg-subtle); color: var(--color-text-muted); }
.principles { padding-left: 1.25em; max-width: var(--layout-measure); display: grid; gap: 12px; }
.principles small { color: var(--color-text-subtle); }
.swatches { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 16px; }
.swatch .chip-color { height: 64px; border-radius: var(--radius-md); border: var(--border-width-hairline) solid var(--color-border-default); }
.swatch code { display: block; font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-text-muted); margin-top: 6px; overflow-wrap: anywhere; }
.swatch strong { display: block; font-size: var(--text-sm); margin-top: 6px; }
.ramp { display: grid; grid-template-columns: 88px repeat(11, minmax(0, 1fr)); gap: 4px; align-items: center; }
.ramp div { height: 40px; border-radius: 4px; }
.ramp div.anchor { outline: 2px solid var(--color-text-default); outline-offset: 2px; }
.ramp span { font-size: var(--text-sm); color: var(--color-text-muted); }
@media (max-width: 560px) { .ramp { grid-template-columns: repeat(11, minmax(0, 1fr)); } .ramp span { grid-column: 1 / -1; } .ramp div { height: 28px; } }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: var(--text-sm); }
th, td { text-align: left; padding: 8px 12px; border-bottom: var(--border-width-hairline) solid var(--color-border-default); vertical-align: top; }
th { background: var(--color-bg-subtle); font-weight: var(--font-weight-semibold); }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
.type-row { display: grid; grid-template-columns: minmax(0, 200px) minmax(0, 1fr); gap: 24px; align-items: baseline; padding-block: 16px; border-bottom: var(--border-width-hairline) solid var(--color-border-default); }
.type-row .meta { font-size: var(--text-xs); color: var(--color-text-muted); font-family: var(--font-mono); }
.type-row > :last-child { min-width: 0; overflow-wrap: anywhere; }
@media (max-width: 640px) { .type-row { grid-template-columns: 1fr; gap: 4px; } }
.space-row { display: grid; grid-template-columns: 72px 1fr; gap: 16px; align-items: center; }
.space-row div { height: 12px; background: var(--color-primary-default); border-radius: 2px; max-width: 100%; }
.shape-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 16px; }
.shape-grid div { height: 88px; background: var(--color-bg-surface); border: var(--border-width-hairline) solid var(--color-border-default); display: grid; place-items: center; font-size: var(--text-sm); color: var(--color-text-muted); }
.row { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; }
.btn { font: inherit; font-family: var(--font-body); font-weight: var(--font-weight-semibold); font-size: var(--text-base);
  padding: var(--space-2) var(--space-4); border-radius: var(--radius-control); border: var(--border-width-default) solid transparent;
  cursor: pointer; transition: background-color var(--duration-fast) var(--ease-standard), border-color var(--duration-fast) var(--ease-standard); }
.btn:focus-visible, input:focus-visible { outline: 2px solid var(--color-border-focus); outline-offset: 2px; }
.btn-primary { background: var(--color-primary-default); color: var(--color-primary-on); }
.btn-primary:hover { background: var(--color-primary-hover); }
.btn-accent { background: var(--color-accent-default); color: var(--color-accent-on); }
.btn-accent:hover { background: var(--color-accent-hover); }
.btn-secondary { background: transparent; color: var(--color-text-default); border-color: var(--color-border-strong); }
.btn-secondary:hover { background: var(--color-bg-subtle); }
.btn-ghost { background: transparent; color: var(--color-text-link); }
.field { display: grid; gap: 6px; max-width: 360px; }
.field label { color: var(--color-text-muted); }
.field input { font: inherit; color: var(--color-text-default); background: var(--color-bg-surface); border: var(--border-width-hairline) solid var(--color-border-strong); border-radius: var(--radius-md); padding: var(--space-2) var(--space-3); }
.field small { color: var(--color-text-subtle); font-size: var(--text-sm); }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: var(--layout-gutter); }
.card { background: var(--color-bg-surface); border: var(--border-width-hairline) solid var(--color-border-default); border-radius: var(--radius-lg); overflow: hidden; box-shadow: var(--shadow-sm); transition: box-shadow var(--duration-base) var(--ease-standard); }
.card:hover { box-shadow: var(--shadow-md); }
.card .media { aspect-ratio: 16 / 9; background: linear-gradient(135deg, var(--color-primary-subtle), var(--color-accent-subtle)); }
.card .body { padding: var(--space-5); display: grid; gap: var(--space-2); }
.badge { display: inline-block; padding: 2px 10px; border-radius: var(--radius-full); }
.alert { padding: var(--space-3) var(--space-4); border-left: 3px solid; border-radius: var(--radius-sm); }
.article { max-width: var(--layout-measure); display: grid; gap: var(--space-4); }
.article blockquote { border-left: 3px solid var(--color-accent-default); padding-left: var(--space-5); margin-block: var(--space-4); }
.article a { color: var(--color-text-link); text-underline-offset: 0.2em; }
.dodont { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: var(--layout-gutter); }
.dodont ul { padding-left: 1.2em; display: grid; gap: 8px; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
"""


CARDS = [  # (section id, Design System pane group, file, title)
    ("principles", "Brand", "brand-principles.html", "Principles"),
    ("voice", "Brand", "brand-voice.html", "Voice & rules"),
    ("color", "Colors", "colors.html", "Color"),
    ("type", "Type", "type.html", "Typography"),
    ("space", "Spacing", "spacing.html", "Space & shape"),
    ("components", "Components", "components.html", "Components"),
    ("provenance", "Brand", "provenance.html", "Provenance"),
]


def cards(s: dict) -> dict[str, str]:
    """One self-contained preview card per section, for a claude.ai/design design-system project.
    The first line carries the @dsCard marker the Design System pane indexes."""
    page = preview_html(s)
    head = page.split("<body>", 1)[0]
    out = {}
    for sid, group, fname, title in CARDS:
        m = re.search(rf'<section id="{sid}">.*?</section>', page, re.S)
        if not m:
            continue
        doc_head = re.sub(r"<title>.*?</title>", f"<title>{html.escape(s['name'])} · {html.escape(title)}</title>", head, count=1)
        out[fname] = (f'<!-- @dsCard group="{group}" -->\n{doc_head}<body>\n<main class="wrap">\n{m.group(0)}\n'
                      "</main>\n</body>\n</html>\n")
    return out


def _swatch(name: str, s: dict) -> str:
    lv, dv = s["color"]["values"]["light"][name], s["color"]["values"]["dark"][name]
    var = f"--color-{name.replace('.', '-')}"
    return (f'<div class="swatch"><div class="chip-color" style="background:var({var})"></div>'
            f'<strong>{html.escape(name)}</strong><code>{lv} · {dv}</code></div>')


def preview_html(s: dict) -> str:
    e = html.escape
    col, ty, lay, g = s["color"], s["typography"], s["layout"], s["guidance"]
    corpus = s.get("corpus", {})
    roles = ", ".join(f"{v} {k}{'s' if v != 1 else ''}" for k, v in (corpus.get("roles") or {}).items())
    css = tokens_css(s)
    for st in ty["styles"]:
        if st["px"] >= 40:
            lo = max(28, round(st["px"] * 0.45))
            css += (f".text-{st['name']} {{ font-size: clamp({lo / 16:g}rem, {st['px'] / 12.8:.2f}vw, "
                    f"{st['px'] / 16:g}rem); }}\n")
    parts = []
    parts.append(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(s['name'])} Design System</title>
<meta name="description" content="{e(s['name'])}: a design system distilled by design-dna from {corpus.get('sources', 0)} design sources.">
{_font_links(s)}
<style>
{css}
{PAGE_CSS}
</style>
</head>
<body>
<header class="topbar"><div class="wrap">
  <span class="text-label">{e(s['name'])}</span>
  <nav aria-label="Sections"><a href="#principles">Principles</a><a href="#color">Color</a><a href="#type">Type</a><a href="#space">Space</a><a href="#components">Components</a><a href="#provenance">Provenance</a></nav>
  <button class="btn btn-secondary" id="theme-toggle" type="button" aria-label="Toggle light and dark theme">Theme</button>
</div></header>
<main class="wrap">
<section class="hero">
  <p class="text-label kicker">Design system · design-dna</p>
  <h1 class="text-display-xl">{e(s['name'])}</h1>
  <p class="text-body-lg lede">Distilled from {corpus.get('sources', 0)} sources ({e(roles)}). Every value below traces back to the corpus. See the provenance section at the end.</p>
  <div class="chips">{''.join(f'<span class="chip">{e(m)}</span>' for m in g['mood'][:8])}</div>
</section>
<section id="principles">
  <h2 class="text-heading-1">Principles</h2>
  <ol class="principles">{''.join(f"<li>{e(p['text'])} <small>{'· ' + str(p['sources']) + (' sources' if p['sources'] != 1 else ' source') if p.get('sources') else '· measured'}</small></li>" for p in g['principles'][:10])}</ol>
</section>
<section id="color">
  <h2 class="text-heading-1">Color</h2>
  <p class="lede">Primary {e(col['names']['primary'])} <code>{col['primary']}</code>, accent {e(col['names']['accent'])} <code>{col['accent']}</code>, on a {e(col['names']['paper'])} canvas. Values are shown as light · dark.</p>
  <div class="swatches">{''.join(_swatch(n, s) for n in col['semantic']['light'])}</div>
  <h3 class="text-heading-3">Palette</h3>
  <div style="display:grid;gap:10px">""")
    for group, ramp in col["ramps"].items():
        anchor = col["anchors"].get(group)
        cells = "".join(f'<div class="{"anchor" if st == anchor else ""}" style="background:var(--color-{group}-{st})" title="{group} {st} {ramp[st]}"></div>'
                        for st in C.STEPS)
        parts.append(f'<div class="ramp"><span>{group}</span>{cells}</div>')
    parts.append("""</div>
  <h3 class="text-heading-3">Contrast</h3>
  <div class="table-wrap"><table><thead><tr><th>Mode</th><th>Pair</th><th>Ratio</th><th>Target</th></tr></thead><tbody>""")
    for r in col["contrast"]:
        parts.append(f"<tr><td>{r['mode']}</td><td><code>{r['fg']}</code> on <code>{r['bg']}</code></td>"
                     f"<td class='num'>{r['ratio']}:1</td><td class='num'>{r['target']}:1 {'✓' if r['pass'] else '⚠'}</td></tr>")
    parts.append(f"""</tbody></table></div>
</section>
<section id="type">
  <h2 class="text-heading-1">Typography</h2>
  <p class="lede">{e(ty['families']['display']['name'])} for display, {e(ty['families']['body']['name'])} for text, {e(ty['families']['mono']['name'])} for code. Base {ty['base']}px on a {ty['ratio']} scale.</p>""")
    samples = {"code": "const system = learn(corpus);", "label": "Section label", "caption": "Figure 1. Caption text sits quietly under images.",
               "quote": "“Good design is as little design as possible.”"}
    for st in ty["styles"]:
        fam = ty["families"][st["family"]]
        text = samples.get(st["name"], "Form follows the reader" if st["px"] >= 24 else
                           "Body copy is set for long, comfortable reading, with a measured line length and generous leading.")
        parts.append(f'<div class="type-row"><div class="meta">{st["name"]}<br>{e(fam["web"])} {st["weight_value"]} · {st["px"]}px / {st["lh_value"]}</div>'
                     f'<div class="text-{st["name"]}">{e(text)}</div></div>')
    parts.append("""</section>
<section id="space">
  <h2 class="text-heading-1">Space &amp; shape</h2>
  <div style="display:grid;gap:8px">""")
    for k, v in s["space"].items():
        if v:
            parts.append(f'<div class="space-row"><code>space-{k}</code><div style="width:{v}px"></div></div>')
    parts.append('</div><div class="shape-grid">')
    for k, v in s["shape"]["radius"].items():
        if k in ("none", "full"):
            continue
        parts.append(f'<div style="border-radius:var(--radius-{k})">radius-{k} · {v}px</div>')
    for k in s["shadow"]:
        parts.append(f'<div style="box-shadow:var(--shadow-{k});border-radius:var(--radius-md)">shadow-{k}</div>')
    parts.append("""</div>
</section>
<section id="components">
  <h2 class="text-heading-1">Components</h2>
  <div class="row">
    <button class="btn btn-primary" type="button">Primary action</button>
    <button class="btn btn-accent" type="button">Accent</button>
    <button class="btn btn-secondary" type="button">Secondary</button>
    <button class="btn btn-ghost" type="button">Ghost link</button>
  </div>
  <div class="field">
    <label class="text-label" for="demo-email">Email</label>
    <input id="demo-email" type="email" placeholder="you@studio.com">
    <small>We’ll only use this to send the brief.</small>
  </div>
  <div class="row">""")
    for st in ("success", "warning", "danger", "info"):
        parts.append(f'<span class="badge text-label" style="background:var(--color-{st}-subtle);color:var(--color-{st}-text)">{st}</span>')
    parts.append('</div><div style="display:grid;gap:12px;max-width:640px">')
    for st, msg in (("success", "Tokens exported to Figma."), ("warning", "Two briefs disagree on the primary color."),
                    ("danger", "Contrast below 4.5:1 on this pair."), ("info", "Three new sources since the last run.")):
        parts.append(f'<div class="alert" style="background:var(--color-{st}-subtle);border-color:var(--color-{st}-default);color:var(--color-{st}-text)">{msg}</div>')
    parts.append("""</div>
  <div class="cards">
    <article class="card"><div class="media"></div><div class="body"><span class="text-label kicker">Case study</span><h3 class="text-heading-3">A system from a stack of references</h3><p class="text-body-sm muted">Cards sit on the surface color with a hairline border.</p></div></article>
    <article class="card"><div class="media"></div><div class="body"><span class="text-label kicker">Report</span><h3 class="text-heading-3">Measured, not guessed</h3><p class="text-body-sm muted">Margins, measure and scale are taken from the corpus.</p></div></article>
    <article class="card"><div class="media"></div><div class="body"><span class="text-label kicker">Magazine</span><h3 class="text-heading-3">Hierarchy you can feel</h3><p class="text-body-sm muted">Display sizes follow the ratio learned from real headlines.</p></div></article>
  </div>
  <div class="article">
    <span class="text-label kicker">Feature</span>
    <h3 class="text-heading-1">An article layout, set in the system</h3>
    <p class="text-caption muted">By the design team · 6 min read</p>
    <p class="text-body">Running text holds to the learned measure, so lines stay comfortable to read. Paragraph spacing follows the stack gap. Links such as <a href="#provenance">this one</a> use the link token, which is tested for contrast in both themes.</p>
    <blockquote class="text-quote">Pull quotes borrow the display face and hang off an accent rule.</blockquote>
    <p class="text-body">Emphasis comes from type and space before color, which matches how the corpus uses its palette.</p>
  </div>
  <div class="table-wrap"><table>
    <thead><tr><th>Source</th><th>Role</th><th class="num">Pages</th><th class="num">Weight</th></tr></thead>
    <tbody><tr><td>Annual report</td><td>report</td><td class="num">48</td><td class="num">0.9</td></tr><tr><td>Spring issue</td><td>magazine</td><td class="num">112</td><td class="num">1.0</td></tr><tr><td>Studio folio</td><td>portfolio</td><td class="num">24</td><td class="num">1.2</td></tr></tbody>
  </table></div>
</section>""")
    if g["dos"] or g["donts"] or g["voice"]:
        parts.append('<section id="voice"><h2 class="text-heading-1">Voice &amp; rules</h2>')
        if g["voice"]:
            parts.append(f'<div class="chips">{"".join(f"<span class=chip>{e(v)}</span>" for v in g["voice"][:8])}</div>')
        parts.append('<div class="dodont">')
        parts.append(f'<div><h3 class="text-heading-3">Do</h3><ul>{"".join(f"<li>{e(d)}</li>" for d in g["dos"])}</ul></div>')
        parts.append(f'<div><h3 class="text-heading-3">Don’t</h3><ul>{"".join(f"<li>{e(d)}</li>" for d in g["donts"])}</ul></div>')
        parts.append("</div></section>")
    parts.append('<section id="provenance"><h2 class="text-heading-1">Provenance</h2><div class="table-wrap"><table><thead><tr><th>Decision</th><th>Where it came from</th></tr></thead><tbody>')
    for k, v in s["provenance"].items():
        parts.append(f"<tr><td><code>{e(k)}</code></td><td>{e(v)}</td></tr>")
    parts.append("</tbody></table></div>")
    items = corpus.get("items") or []
    if items:
        parts.append('<div class="table-wrap"><table><thead><tr><th>Source</th><th>Role</th><th>Kind</th><th>Reviewed</th></tr></thead><tbody>')
        for it in items:
            parts.append(f"<tr><td>{e(str(it.get('name')))}</td><td>{e(str(it.get('role')))}</td><td>{e(str(it.get('kind')))}</td>"
                         f"<td>{'yes' if it.get('observed') else '—'}</td></tr>")
        parts.append("</tbody></table></div>")
    parts.append("""</section>
</main>
<script>
(function () {
  var root = document.documentElement, key = "design-dna-theme";
  try { var saved = localStorage.getItem(key); if (saved) root.setAttribute("data-theme", saved); } catch (e) {}
  document.getElementById("theme-toggle").addEventListener("click", function () {
    var cur = root.getAttribute("data-theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    var next = cur === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem(key, next); } catch (e) {}
  });
})();
</script>
</body>
</html>
""")
    return "\n".join(parts)
