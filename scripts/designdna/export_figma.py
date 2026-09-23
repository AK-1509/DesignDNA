"""Figma: variables/styles spec + ready-to-run Plugin API scripts for the Figma MCP ``use_figma`` tool.

Three idempotent scripts (safe to re-run; they update by name):
  01-variables.js    collections Primitives / Color (Light, Dark) / Typography / Spacing
  02-styles.js       text styles (font picked from what the Figma file can load) + effect styles
  03-foundations.js  a "Foundations" page with swatches bound to variables, light & dark side by side
"""
from __future__ import annotations

import json
import re

from . import color as C

PRIM, SEM, TYPO, SPACE = "Primitives", "Color", "Typography", "Spacing"
SCOPES = {"bg": ["FRAME_FILL", "SHAPE_FILL"], "text": ["TEXT_FILL"], "border": ["STROKE_COLOR"],
          "primary": ["FRAME_FILL", "SHAPE_FILL", "STROKE_COLOR"], "accent": ["FRAME_FILL", "SHAPE_FILL", "STROKE_COLOR"]}


def _rgba(hex_value: str, a: float = 1.0) -> dict:
    r, g, b = C.hex_to_rgb(hex_value)
    return {"r": round(r, 5), "g": round(g, 5), "b": round(b, 5), "a": a}


def _prim_name(ref: str) -> str:
    group, key = ref.split(".")
    return f"color/base/{key}" if group == "base" else f"color/{group}/{key}"


def spec(s: dict) -> dict:
    col, ty = s["color"], s["typography"]
    prim = []
    for group, ramp in col["ramps"].items():
        for step, hx in ramp.items():
            prim.append({"name": f"color/{group}/{step}", "type": "COLOR", "values": {"Value": _rgba(hx)},
                         "scopes": [], "codeSyntax": f"var(--color-{group}-{step})"})
    for k, hx in col["base"].items():
        prim.append({"name": f"color/base/{k}", "type": "COLOR", "values": {"Value": _rgba(hx)},
                     "scopes": [], "codeSyntax": f"var(--color-base-{k})"})
    sem = []
    for name, ref in col["semantic"]["light"].items():
        group = name.split(".")[0]
        scopes = SCOPES.get(group, ["FRAME_FILL", "SHAPE_FILL", "STROKE_COLOR"])
        if name.endswith(".on") or name.endswith(".text"):
            scopes = ["TEXT_FILL", "SHAPE_FILL"]
        sem.append({"name": name.replace(".", "/"), "type": "COLOR", "scopes": scopes,
                    "codeSyntax": f"var(--color-{name.replace('.', '-')})",
                    "values": {"Light": {"alias": _prim_name(ref), "collection": PRIM},
                               "Dark": {"alias": _prim_name(col["semantic"]["dark"][name]), "collection": PRIM}}})
    typo = []
    for role, fam in ty["families"].items():
        typo.append({"name": f"font/family/{role}", "type": "STRING", "values": {"Value": fam["web"]},
                     "scopes": ["FONT_FAMILY"], "description": f"Brand face: {fam['name']}",
                     "codeSyntax": f"var(--font-{role})"})
    for k, w in ty["weights"].items():
        typo.append({"name": f"font/weight/{k}", "type": "FLOAT", "values": {"Value": w}, "scopes": ["FONT_WEIGHT"],
                     "codeSyntax": f"var(--font-weight-{k})"})
    for k, px in ty["sizes"].items():
        typo.append({"name": f"font/size/{k}", "type": "FLOAT", "values": {"Value": px}, "scopes": ["FONT_SIZE"],
                     "codeSyntax": f"var(--text-{k})"})
    space = []
    for k, px in s["space"].items():
        space.append({"name": f"space/{k}", "type": "FLOAT", "values": {"Value": px}, "scopes": ["GAP", "WIDTH_HEIGHT"],
                      "codeSyntax": f"var(--space-{k})"})
    for k, px in s["shape"]["radius"].items():
        space.append({"name": f"radius/{k}", "type": "FLOAT", "values": {"Value": px}, "scopes": ["CORNER_RADIUS"],
                      "codeSyntax": f"var(--radius-{k})"})
    for k, px in s["shape"]["border_width"].items():
        space.append({"name": f"border-width/{k}", "type": "FLOAT", "values": {"Value": px}, "scopes": ["STROKE_FLOAT"],
                      "codeSyntax": f"var(--border-width-{k})"})
    lay = s["layout"]
    for k in ("margin", "margin_mobile", "gutter", "max_width", "section_gap", "stack_gap"):
        space.append({"name": f"layout/{k.replace('_', '-')}", "type": "FLOAT", "values": {"Value": lay[k]},
                      "scopes": ["GAP", "WIDTH_HEIGHT"], "codeSyntax": f"var(--layout-{k.replace('_', '-')})"})

    text_styles = []
    for st in ty["styles"]:
        fam = ty["families"][st["family"]]
        group, _, rest = st["name"].partition("-")
        pretty = "/".join(x.upper() if re.fullmatch(r"\d?x[sl]|\d+xl|sm|lg", x) else x.capitalize()
                          for x in [group] + ([rest] if rest else []))
        text_styles.append({"name": pretty, "families": fam["figma"], "weight": st["weight_value"], "italic": st["italic"],
                            "size": st["px"], "lineHeightPct": round(st["lh_value"] * 100, 1),
                            "letterSpacingPct": round(st["ls_value"] * 100, 2), "textCase": st["case"],
                            "sizeVar": f"font/size/{st['size']}" if st.get("size") else None,
                            "description": f"{fam['name']} {st['weight_value']} · {st['px']}px/{st['lh_value']}"})
    effects = [{"name": f"Shadow/{k.upper()}", "effects": [{"color": _rgba(sh["color"], sh["alpha"]),
                                                           "offset": {"x": sh["x"], "y": sh["y"]},
                                                           "radius": sh["blur"], "spread": sh["spread"]}]}
               for k, sh in s["shadow"].items()]
    return {
        "name": s["name"],
        "collections": [
            {"name": PRIM, "modes": ["Value"], "hidden": True, "variables": prim},
            {"name": SEM, "modes": ["Light", "Dark"], "variables": sem},
            {"name": TYPO, "modes": ["Value"], "variables": typo},
            {"name": SPACE, "modes": ["Value"], "variables": space},
        ],
        "textStyles": text_styles,
        "effectStyles": effects,
        "foundations": {
            "pageName": "Foundations",
            "title": s["name"],
            "subtitle": f"Distilled by design-dna from {s['corpus'].get('sources', 0)} sources",
            "colorCollection": SEM, "primitivesCollection": PRIM,
            "semantic": [v["name"] for v in sem],
            "ramps": {g: [f"color/{g}/{st}" for st in C.STEPS] for g in col["ramps"]},
            "textStyles": [t["name"] for t in text_styles],
            "space": [f"space/{k}" for k in s["space"] if s["space"][k] > 0],
        },
    }


# ---------------------------------------------------------------------------
# Plugin API scripts
# ---------------------------------------------------------------------------

VARIABLES_JS = r"""// design-dna · Figma variables for "__NAME__"
// Run with the Figma MCP `use_figma` tool inside a Figma Design file (load the figma-use skill first).
// Idempotent: re-running updates collections and variables by name.
const DATA = __DATA__;

const report = { created: 0, updated: 0, collections: [], warnings: [] };
const collections = await figma.variables.getLocalVariableCollectionsAsync();
const allVars = await figma.variables.getLocalVariablesAsync();
const k = (colId, name) => colId + "::" + name;
const varIndex = new Map(allVars.map(v => [k(v.variableCollectionId, v.name), v]));
const colByName = new Map();

async function ensureCollection(spec) {
  let col = collections.find(c => c.name === spec.name);
  if (!col) { col = figma.variables.createVariableCollection(spec.name); collections.push(col); }
  const modeIds = {};
  for (const m of spec.modes) {
    const existing = col.modes.find(x => x.name === m);
    if (existing) { modeIds[m] = existing.modeId; continue; }
    const spare = col.modes.find(x => !spec.modes.includes(x.name) && !Object.values(modeIds).includes(x.modeId));
    if (spare) { col.renameMode(spare.modeId, m); modeIds[m] = spare.modeId; continue; }
    try { modeIds[m] = col.addMode(m); }
    catch (e) { report.warnings.push(`Mode "${m}" not added to ${spec.name} (plan limit?): ${e.message}`); }
  }
  if (spec.hidden) { try { col.hiddenFromPublishing = true; } catch (e) {} }
  colByName.set(spec.name, { col, modeIds });
  report.collections.push({ name: spec.name, modes: Object.keys(modeIds) });
  return { col, modeIds };
}

function resolve(val) {
  if (val && typeof val === "object" && "alias" in val) {
    const target = colByName.get(val.collection);
    const v = target && varIndex.get(k(target.col.id, val.alias));
    if (!v) throw new Error(`alias target missing: ${val.collection}/${val.alias}`);
    return figma.variables.createVariableAlias(v);
  }
  return val;
}

for (const spec of DATA.collections) {
  const { col, modeIds } = await ensureCollection(spec);
  for (const vs of spec.variables) {
    let v = varIndex.get(k(col.id, vs.name));
    if (v && v.resolvedType !== vs.type) { v.remove(); v = null; }
    if (!v) { v = figma.variables.createVariable(vs.name, col, vs.type); varIndex.set(k(col.id, vs.name), v); report.created++; }
    else report.updated++;
    for (const [mode, raw] of Object.entries(vs.values)) {
      if (!modeIds[mode]) continue;
      try { v.setValueForMode(modeIds[mode], resolve(raw)); }
      catch (e) { report.warnings.push(`${spec.name}/${vs.name} [${mode}]: ${e.message}`); }
    }
    if (vs.description) v.description = vs.description;
    if (vs.scopes) { try { v.scopes = vs.scopes; } catch (e) { report.warnings.push(`scopes ${vs.name}: ${e.message}`); } }
    if (vs.codeSyntax) { try { v.setVariableCodeSyntax("WEB", vs.codeSyntax); } catch (e) {} }
    if (spec.hidden) { try { v.hiddenFromPublishing = true; } catch (e) {} }
  }
}
report.warnings = report.warnings.slice(0, 25);
return report;
"""

STYLES_JS = r"""// design-dna · Figma text & effect styles for "__NAME__"
// Run after 01-variables.js with the Figma MCP `use_figma` tool. Idempotent (updates styles by name).
const DATA = __DATA__;

const report = { textStyles: 0, effectStyles: 0, substitutions: {}, warnings: [] };
const available = await figma.listAvailableFontsAsync();
const byFamily = new Map();
for (const f of available) {
  const key = f.fontName.family.toLowerCase();
  if (!byFamily.has(key)) byFamily.set(key, []);
  byFamily.get(key).push(f.fontName);
}
function styleWeight(style) {
  const s = style.toLowerCase().replace(/[\s_-]/g, "");
  if (/hairline|thin/.test(s)) return 100;
  if (/extralight|ultralight/.test(s)) return 200;
  if (/semibold|demibold|demi/.test(s)) return 600;
  if (/extrabold|ultrabold|heavy/.test(s)) return 800;
  if (/black/.test(s)) return 900;
  if (/light/.test(s)) return 300;
  if (/bold/.test(s)) return 700;
  if (/medium/.test(s)) return 500;
  return 400;
}
function pickFont(families, weight, italic) {
  for (const fam of families) {
    const styles = byFamily.get(String(fam).toLowerCase());
    if (!styles || !styles.length) continue;
    const matching = styles.filter(s => /italic|oblique/i.test(s.style) === !!italic);
    const pool = matching.length ? matching : styles;
    let best = pool[0], bestD = Infinity;
    for (const s of pool) { const d = Math.abs(styleWeight(s.style) - weight); if (d < bestD) { bestD = d; best = s; } }
    return best;
  }
  return { family: "Inter", style: "Regular" };
}

const vars = await figma.variables.getLocalVariablesAsync();
const varByName = new Map(vars.map(v => [v.name, v]));
const textStyles = await figma.getLocalTextStylesAsync();
for (const ts of DATA.textStyles) {
  const font = pickFont(ts.families, ts.weight, ts.italic);
  try { await figma.loadFontAsync(font); }
  catch (e) { report.warnings.push(`font ${font.family} ${font.style}: ${e.message}`); continue; }
  if (font.family.toLowerCase() !== String(ts.families[0]).toLowerCase()) report.substitutions[ts.families[0]] = font.family;
  let st = textStyles.find(s => s.name === ts.name);
  if (!st) { st = figma.createTextStyle(); st.name = ts.name; textStyles.push(st); }
  st.fontName = font;
  st.fontSize = ts.size;
  st.lineHeight = { unit: "PERCENT", value: ts.lineHeightPct };
  st.letterSpacing = { unit: "PERCENT", value: ts.letterSpacingPct };
  st.textCase = ts.textCase;
  if (ts.description) st.description = ts.description;
  if (ts.sizeVar && varByName.has(ts.sizeVar)) {
    try { st.setBoundVariable("fontSize", varByName.get(ts.sizeVar)); } catch (e) {}
  }
  report.textStyles++;
}

const effectStyles = await figma.getLocalEffectStylesAsync();
for (const es of DATA.effectStyles) {
  let st = effectStyles.find(s => s.name === es.name);
  if (!st) { st = figma.createEffectStyle(); st.name = es.name; }
  st.effects = es.effects.map(e => ({ type: "DROP_SHADOW", color: e.color, offset: e.offset, radius: e.radius,
                                      spread: e.spread, visible: true, blendMode: "NORMAL" }));
  report.effectStyles++;
}
return report;
"""

FOUNDATIONS_JS = r"""// design-dna · "Foundations" page for "__NAME__"
// Run after 01-variables.js and 02-styles.js with the Figma MCP `use_figma` tool.
// Rebuilds its own frame on each run; everything is bound to variables and text styles.
const DATA = __DATA__;

let page = figma.root.children.find(p => p.name === DATA.pageName);
if (!page) { page = figma.createPage(); page.name = DATA.pageName; }
await figma.setCurrentPageAsync(page);
for (const n of [...page.children]) { if (n.getPluginData("design-dna") === "foundations") n.remove(); }

const cols = await figma.variables.getLocalVariableCollectionsAsync();
const vars = await figma.variables.getLocalVariablesAsync();
const colorCol = cols.find(c => c.name === DATA.colorCollection);
const primCol = cols.find(c => c.name === DATA.primitivesCollection);
const spaceCol = cols.find(c => c.name === "Spacing");
const find = (col, name) => col && vars.find(v => v.variableCollectionId === col.id && v.name === name);
const styles = await figma.getLocalTextStylesAsync();
const styleByName = new Map(styles.map(s => [s.name, s]));
for (const s of styles) { try { await figma.loadFontAsync(s.fontName); } catch (e) {} }
await figma.loadFontAsync({ family: "Inter", style: "Regular" });

function paint(variable) {
  return figma.variables.setBoundVariableForPaint({ type: "SOLID", color: { r: 0.5, g: 0.5, b: 0.5 } }, "color", variable);
}
function stack(name, dir, gap, pad) {
  const f = figma.createFrame();
  f.name = name; f.layoutMode = dir; f.itemSpacing = gap;
  f.paddingTop = f.paddingBottom = f.paddingLeft = f.paddingRight = pad || 0;
  f.primaryAxisSizingMode = "AUTO"; f.counterAxisSizingMode = "AUTO"; f.fills = [];
  return f;
}
async function label(chars, styleName, colorVar) {
  const t = figma.createText();
  const st = styleByName.get(styleName);
  if (st) await t.setTextStyleIdAsync(st.id); else t.fontName = { family: "Inter", style: "Regular" };
  t.characters = chars;
  if (colorVar) t.fills = [paint(colorVar)];
  return t;
}
const textDefault = find(colorCol, "text/default");
const textMuted = find(colorCol, "text/muted");

const root = stack(`Foundations — ${DATA.title}`, "VERTICAL", 48, 64);
root.setPluginData("design-dna", "foundations");
const canvas = find(colorCol, "bg/canvas");
if (canvas) root.fills = [paint(canvas)];
root.appendChild(await label(DATA.title, "Display/LG", textDefault));
root.appendChild(await label(DATA.subtitle, "Body/LG", textMuted));

// Semantic colors, light & dark side by side (explicit variable modes)
const modesRow = stack("Semantic color", "HORIZONTAL", 32, 0);
for (const mode of colorCol ? colorCol.modes : []) {
  const panel = stack(mode.name, "VERTICAL", 16, 32);
  try { panel.setExplicitVariableModeForCollection(colorCol, mode.modeId); }
  catch (e) { try { panel.setExplicitVariableModeForCollection(colorCol.id, mode.modeId); } catch (e2) {} }
  if (canvas) panel.fills = [paint(canvas)];
  panel.cornerRadius = 12;
  panel.appendChild(await label(mode.name, "Heading/3", textDefault));
  const grid = stack("swatches", "HORIZONTAL", 12, 0);
  grid.layoutWrap = "WRAP"; grid.counterAxisSpacing = 16; grid.primaryAxisSizingMode = "FIXED"; grid.resize(560, 100);
  for (const name of DATA.semantic) {
    const v = find(colorCol, name);
    if (!v) continue;
    const cell = stack(name, "VERTICAL", 6, 0);
    const sw = figma.createRectangle();
    sw.resize(128, 56); sw.cornerRadius = 6; sw.fills = [paint(v)];
    const border = find(colorCol, "border/default");
    if (border) { sw.strokes = [paint(border)]; sw.strokeWeight = 1; }
    cell.appendChild(sw);
    cell.appendChild(await label(name, "Caption", textMuted));
    grid.appendChild(cell);
  }
  panel.appendChild(grid);
  modesRow.appendChild(panel);
}
root.appendChild(modesRow);

// Primitive ramps
const ramps = stack("Ramps", "VERTICAL", 12, 0);
ramps.appendChild(await label("Palette", "Heading/2", textDefault));
for (const [group, names] of Object.entries(DATA.ramps)) {
  const row = stack(group, "HORIZONTAL", 4, 0);
  row.counterAxisAlignItems = "CENTER";
  const tag = await label(group, "Label", textMuted);
  tag.resize(96, tag.height); tag.textAutoResize = "HEIGHT";
  row.appendChild(tag);
  for (const n of names) {
    const v = find(primCol, n);
    if (!v) continue;
    const r = figma.createRectangle(); r.name = n; r.resize(56, 40); r.fills = [paint(v)];
    row.appendChild(r);
  }
  ramps.appendChild(row);
}
root.appendChild(ramps);

// Type specimens
const type = stack("Type", "VERTICAL", 20, 0);
type.appendChild(await label("Typography", "Heading/2", textDefault));
for (const name of DATA.textStyles) {
  const st = styleByName.get(name);
  if (!st) continue;
  const row = stack(name, "HORIZONTAL", 24, 0);
  row.counterAxisAlignItems = "BASELINE";
  const meta = await label(`${name}\n${st.fontName.family} ${st.fontName.style} · ${Math.round(st.fontSize)}px`, "Caption", textMuted);
  meta.resize(200, meta.height); meta.textAutoResize = "HEIGHT";
  row.appendChild(meta);
  row.appendChild(await label(name.startsWith("Code") ? "const system = learn(corpus);" : "Form follows the reader", name, textDefault));
  type.appendChild(row);
}
root.appendChild(type);

// Spacing
const sp = stack("Spacing", "VERTICAL", 8, 0);
sp.appendChild(await label("Spacing", "Heading/2", textDefault));
const accent = find(colorCol, "primary/default");
for (const n of DATA.space) {
  const v = find(spaceCol, n);
  if (!v) continue;
  const row = stack(n, "HORIZONTAL", 16, 0);
  row.counterAxisAlignItems = "CENTER";
  const t = await label(n, "Caption", textMuted); t.resize(96, t.height); t.textAutoResize = "HEIGHT";
  const bar = figma.createRectangle(); bar.resize(Math.max(1, v.valuesByMode[Object.keys(v.valuesByMode)[0]]), 12);
  try { bar.setBoundVariable("width", v); } catch (e) {}
  if (accent) bar.fills = [paint(accent)];
  row.appendChild(t); row.appendChild(bar);
  sp.appendChild(row);
}
root.appendChild(sp);

page.appendChild(root);
figma.viewport.scrollAndZoomIntoView([root]);
return { page: page.name, frame: root.id, name: root.name };
"""


def scripts(sp: dict) -> dict[str, str]:
    def fill(tpl, data):
        return tpl.replace("__NAME__", sp["name"].replace('"', "'")).replace(
            "__DATA__", json.dumps(data, ensure_ascii=False, indent=1))
    return {
        "01-variables.js": fill(VARIABLES_JS, {"collections": sp["collections"]}),
        "02-styles.js": fill(STYLES_JS, {"textStyles": sp["textStyles"], "effectStyles": sp["effectStyles"]}),
        "03-foundations.js": fill(FOUNDATIONS_JS, sp["foundations"]),
    }
