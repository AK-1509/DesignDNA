// design-dna · Figma text & effect styles for "Meridian"
// Run after 01-variables.js with the Figma MCP `use_figma` tool. Idempotent (updates styles by name).
const DATA = {
 "textStyles": [
  {
   "name": "Display/XL",
   "families": [
    "Playfair Display",
    "Inter"
   ],
   "weight": 700,
   "italic": false,
   "size": 123,
   "lineHeightPct": 110.0,
   "letterSpacingPct": -1.0,
   "textCase": "ORIGINAL",
   "sizeVar": "font/size/3xl",
   "description": "Playfair Display 700 · 123px/1.1"
  },
  {
   "name": "Display/LG",
   "families": [
    "Playfair Display",
    "Inter"
   ],
   "weight": 700,
   "italic": false,
   "size": 76,
   "lineHeightPct": 110.0,
   "letterSpacingPct": -1.0,
   "textCase": "ORIGINAL",
   "sizeVar": "font/size/2xl",
   "description": "Playfair Display 700 · 76px/1.1"
  },
  {
   "name": "Heading/1",
   "families": [
    "Playfair Display",
    "Inter"
   ],
   "weight": 700,
   "italic": false,
   "size": 47,
   "lineHeightPct": 135.0,
   "letterSpacingPct": 0.0,
   "textCase": "ORIGINAL",
   "sizeVar": "font/size/xl",
   "description": "Playfair Display 700 · 47px/1.35"
  },
  {
   "name": "Heading/2",
   "families": [
    "Playfair Display",
    "Inter"
   ],
   "weight": 700,
   "italic": false,
   "size": 37,
   "lineHeightPct": 135.0,
   "letterSpacingPct": 0.0,
   "textCase": "ORIGINAL",
   "sizeVar": null,
   "description": "Playfair Display 700 · 37px/1.35"
  },
  {
   "name": "Heading/3",
   "families": [
    "Playfair Display",
    "Inter"
   ],
   "weight": 600,
   "italic": false,
   "size": 29,
   "lineHeightPct": 135.0,
   "letterSpacingPct": 0.0,
   "textCase": "ORIGINAL",
   "sizeVar": "font/size/lg",
   "description": "Playfair Display 600 · 29px/1.35"
  },
  {
   "name": "Body/LG",
   "families": [
    "Source Serif 4",
    "Inter"
   ],
   "weight": 400,
   "italic": false,
   "size": 29,
   "lineHeightPct": 165.0,
   "letterSpacingPct": 0.0,
   "textCase": "ORIGINAL",
   "sizeVar": "font/size/lg",
   "description": "Source Serif 4 400 · 29px/1.65"
  },
  {
   "name": "Body",
   "families": [
    "Source Serif 4",
    "Inter"
   ],
   "weight": 400,
   "italic": false,
   "size": 18,
   "lineHeightPct": 165.0,
   "letterSpacingPct": 0.0,
   "textCase": "ORIGINAL",
   "sizeVar": "font/size/base",
   "description": "Source Serif 4 400 · 18px/1.65"
  },
  {
   "name": "Body/SM",
   "families": [
    "Source Serif 4",
    "Inter"
   ],
   "weight": 400,
   "italic": false,
   "size": 13,
   "lineHeightPct": 165.0,
   "letterSpacingPct": 0.0,
   "textCase": "ORIGINAL",
   "sizeVar": "font/size/sm",
   "description": "Source Serif 4 400 · 13px/1.65"
  },
  {
   "name": "Label",
   "families": [
    "Source Serif 4",
    "Inter"
   ],
   "weight": 600,
   "italic": false,
   "size": 13,
   "lineHeightPct": 135.0,
   "letterSpacingPct": 8.0,
   "textCase": "UPPER",
   "sizeVar": "font/size/sm",
   "description": "Source Serif 4 600 · 13px/1.35"
  },
  {
   "name": "Caption",
   "families": [
    "Source Serif 4",
    "Inter"
   ],
   "weight": 400,
   "italic": false,
   "size": 11,
   "lineHeightPct": 135.0,
   "letterSpacingPct": 0.0,
   "textCase": "ORIGINAL",
   "sizeVar": "font/size/xs",
   "description": "Source Serif 4 400 · 11px/1.35"
  },
  {
   "name": "Quote",
   "families": [
    "Playfair Display",
    "Inter"
   ],
   "weight": 400,
   "italic": true,
   "size": 47,
   "lineHeightPct": 135.0,
   "letterSpacingPct": 0.0,
   "textCase": "ORIGINAL",
   "sizeVar": "font/size/xl",
   "description": "Playfair Display 400 · 47px/1.35"
  },
  {
   "name": "Code",
   "families": [
    "JetBrains Mono",
    "Inter"
   ],
   "weight": 400,
   "italic": false,
   "size": 13,
   "lineHeightPct": 165.0,
   "letterSpacingPct": 0.0,
   "textCase": "ORIGINAL",
   "sizeVar": "font/size/sm",
   "description": "JetBrains Mono 400 · 13px/1.65"
  }
 ],
 "effectStyles": [
  {
   "name": "Shadow/SM",
   "effects": [
    {
     "color": {
      "r": 0.10196,
      "g": 0.10196,
      "b": 0.10196,
      "a": 0.05
     },
     "offset": {
      "x": 0,
      "y": 1
     },
     "radius": 2,
     "spread": 0
    }
   ]
  },
  {
   "name": "Shadow/MD",
   "effects": [
    {
     "color": {
      "r": 0.10196,
      "g": 0.10196,
      "b": 0.10196,
      "a": 0.06
     },
     "offset": {
      "x": 0,
      "y": 4
     },
     "radius": 12,
     "spread": -2
    }
   ]
  },
  {
   "name": "Shadow/LG",
   "effects": [
    {
     "color": {
      "r": 0.10196,
      "g": 0.10196,
      "b": 0.10196,
      "a": 0.08
     },
     "offset": {
      "x": 0,
      "y": 12
     },
     "radius": 32,
     "spread": -8
    }
   ]
  }
 ]
};

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
