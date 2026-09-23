// design-dna · "Foundations" page for "Meridian"
// Run after 01-variables.js and 02-styles.js with the Figma MCP `use_figma` tool.
// Rebuilds its own frame on each run; everything is bound to variables and text styles.
const DATA = {
 "pageName": "Foundations",
 "title": "Meridian",
 "subtitle": "Distilled by design-dna from 5 sources",
 "colorCollection": "Color",
 "primitivesCollection": "Primitives",
 "semantic": [
  "bg/canvas",
  "bg/surface",
  "bg/subtle",
  "bg/muted",
  "bg/inverse",
  "text/default",
  "text/muted",
  "text/subtle",
  "text/inverse",
  "text/link",
  "border/default",
  "border/strong",
  "border/focus",
  "primary/default",
  "primary/hover",
  "primary/subtle",
  "primary/on",
  "accent/default",
  "accent/hover",
  "accent/subtle",
  "accent/on",
  "success/default",
  "success/subtle",
  "success/text",
  "warning/default",
  "warning/subtle",
  "warning/text",
  "danger/default",
  "danger/subtle",
  "danger/text",
  "info/default",
  "info/subtle",
  "info/text"
 ],
 "ramps": {
  "brand": [
   "color/brand/50",
   "color/brand/100",
   "color/brand/200",
   "color/brand/300",
   "color/brand/400",
   "color/brand/500",
   "color/brand/600",
   "color/brand/700",
   "color/brand/800",
   "color/brand/900",
   "color/brand/950"
  ],
  "accent": [
   "color/accent/50",
   "color/accent/100",
   "color/accent/200",
   "color/accent/300",
   "color/accent/400",
   "color/accent/500",
   "color/accent/600",
   "color/accent/700",
   "color/accent/800",
   "color/accent/900",
   "color/accent/950"
  ],
  "neutral": [
   "color/neutral/50",
   "color/neutral/100",
   "color/neutral/200",
   "color/neutral/300",
   "color/neutral/400",
   "color/neutral/500",
   "color/neutral/600",
   "color/neutral/700",
   "color/neutral/800",
   "color/neutral/900",
   "color/neutral/950"
  ],
  "success": [
   "color/success/50",
   "color/success/100",
   "color/success/200",
   "color/success/300",
   "color/success/400",
   "color/success/500",
   "color/success/600",
   "color/success/700",
   "color/success/800",
   "color/success/900",
   "color/success/950"
  ],
  "warning": [
   "color/warning/50",
   "color/warning/100",
   "color/warning/200",
   "color/warning/300",
   "color/warning/400",
   "color/warning/500",
   "color/warning/600",
   "color/warning/700",
   "color/warning/800",
   "color/warning/900",
   "color/warning/950"
  ],
  "danger": [
   "color/danger/50",
   "color/danger/100",
   "color/danger/200",
   "color/danger/300",
   "color/danger/400",
   "color/danger/500",
   "color/danger/600",
   "color/danger/700",
   "color/danger/800",
   "color/danger/900",
   "color/danger/950"
  ],
  "info": [
   "color/info/50",
   "color/info/100",
   "color/info/200",
   "color/info/300",
   "color/info/400",
   "color/info/500",
   "color/info/600",
   "color/info/700",
   "color/info/800",
   "color/info/900",
   "color/info/950"
  ]
 },
 "textStyles": [
  "Display/XL",
  "Display/LG",
  "Heading/1",
  "Heading/2",
  "Heading/3",
  "Body/LG",
  "Body",
  "Body/SM",
  "Label",
  "Caption",
  "Quote",
  "Code"
 ],
 "space": [
  "space/0-5",
  "space/1",
  "space/1-5",
  "space/2",
  "space/3",
  "space/4",
  "space/5",
  "space/6",
  "space/8",
  "space/10",
  "space/12",
  "space/16",
  "space/20",
  "space/24",
  "space/32"
 ]
};

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
