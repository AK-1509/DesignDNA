"""Design tokens: W3C DTCG JSON (primitives, light/dark semantics, typography) and CSS custom properties."""
from __future__ import annotations

from . import color as C


def _hex_alpha(hex_value: str, alpha: float) -> str:
    return hex_value.upper() + f"{round(alpha * 255):02X}"


def _rgba(hex_value: str, alpha: float) -> str:
    r, g, b = (round(x * 255) for x in C.hex_to_rgb(hex_value))
    return f"rgba({r}, {g}, {b}, {alpha:g})"


class DTCG:
    """Builds DTCG token values. ``fmt='legacy'`` uses string values ("#RRGGBB", "16px")
    understood by most tools today; ``fmt='2025'`` uses the object values of the 2025.10 spec."""

    def __init__(self, fmt: str = "legacy"):
        self.fmt = fmt

    def color(self, hex_value: str, alpha: float = 1.0):
        if self.fmt == "legacy":
            return hex_value.upper() if alpha >= 1 else _hex_alpha(hex_value, alpha)
        r, g, b = C.hex_to_rgb(hex_value)
        v = {"colorSpace": "srgb", "components": [round(r, 4), round(g, 4), round(b, 4)], "hex": hex_value.upper()}
        if alpha < 1:
            v["alpha"] = alpha
        return v

    def dim(self, px: float, unit: str = "px"):
        return f"{px:g}{unit}" if self.fmt == "legacy" else {"value": px, "unit": unit}

    def duration(self, ms: float):
        return f"{ms:g}ms" if self.fmt == "legacy" else {"value": ms, "unit": "ms"}


def _ref(ref: str) -> str:
    group, key = ref.split(".")
    return "{color.base.%s}" % key if group == "base" else "{color.%s.%s}" % (group, key)


def _set(tree: dict, path: list[str], token: dict) -> None:
    for p in path[:-1]:
        tree = tree.setdefault(p, {})
    tree[path[-1]] = token


def primitives(s: dict, d: DTCG) -> dict:
    t: dict = {}
    col = s["color"]
    for group, ramp in col["ramps"].items():
        for step, hx in ramp.items():
            tok = {"$type": "color", "$value": d.color(hx)}
            if col["anchors"].get(group) == step:
                tok["$description"] = "Anchor: source color from the corpus"
            _set(t, ["color", group, str(step)], tok)
    for key, hx in col["base"].items():
        _set(t, ["color", "base", key], {"$type": "color", "$value": d.color(hx)})
    ty = s["typography"]
    for role, fam in ty["families"].items():
        _set(t, ["font", "family", role], {"$type": "fontFamily", "$value": [fam["name"]] + ([fam["substitute"]] if fam["substitute"] else []),
                                             "$description": f"{fam['category']}; web/Figma: {fam['web']}"})
    for k, w in ty["weights"].items():
        _set(t, ["font", "weight", k], {"$type": "fontWeight", "$value": w})
    for k, px in ty["sizes"].items():
        _set(t, ["font", "size", k], {"$type": "dimension", "$value": d.dim(px)})
    for k, v in ty["line_height"].items():
        _set(t, ["font", "line-height", k], {"$type": "number", "$value": v})
    for k, v in ty["tracking"].items():
        _set(t, ["font", "letter-spacing", k], {"$type": "dimension", "$value": d.dim(round(v * ty["base"], 2)),
                                                 "$extensions": {"design-dna": {"em": v}}})
    for k, px in s["space"].items():
        _set(t, ["space", k], {"$type": "dimension", "$value": d.dim(px)})
    for k, px in s["shape"]["radius"].items():
        _set(t, ["radius", k], {"$type": "dimension", "$value": d.dim(px)})
    for k, px in s["shape"]["border_width"].items():
        _set(t, ["border-width", k], {"$type": "dimension", "$value": d.dim(px)})
    for k, sh in s["shadow"].items():
        _set(t, ["shadow", k], {"$type": "shadow", "$value": {"color": d.color(sh["color"], sh["alpha"]),
                                                              "offsetX": d.dim(sh["x"]), "offsetY": d.dim(sh["y"]),
                                                              "blur": d.dim(sh["blur"]), "spread": d.dim(sh["spread"])}})
    for k, ms in s["motion"]["duration"].items():
        _set(t, ["duration", k], {"$type": "duration", "$value": d.duration(ms)})
    for k, bz in s["motion"]["easing"].items():
        _set(t, ["easing", k], {"$type": "cubicBezier", "$value": bz})
    lay = s["layout"]
    for k in ("margin", "margin_mobile", "gutter", "max_width", "section_gap", "stack_gap"):
        _set(t, ["layout", k.replace("_", "-")], {"$type": "dimension", "$value": d.dim(lay[k])})
    _set(t, ["layout", "columns"], {"$type": "number", "$value": lay["columns"]})
    _set(t, ["layout", "measure"], {"$type": "number", "$value": lay["measure"], "$description": "Body text measure in ch"})
    return t


def semantic(s: dict, mode: str) -> dict:
    t: dict = {}
    for name, ref in s["color"]["semantic"][mode].items():
        _set(t, ["color"] + name.split("."), {"$type": "color", "$value": _ref(ref)})
    return t


def typography(s: dict, d: DTCG) -> dict:
    t: dict = {}
    ty = s["typography"]
    for st in ty["styles"]:
        size = "{font.size.%s}" % st["size"] if st.get("size") else d.dim(st["px"])
        _set(t, ["typography", st["name"]], {
            "$type": "typography",
            "$value": {"fontFamily": "{font.family.%s}" % st["family"], "fontSize": size,
                       "fontWeight": "{font.weight.%s}" % st["weight"], "lineHeight": st["lh_value"],
                       "letterSpacing": d.dim(round(st["ls_value"] * st["px"], 2))},
            "$extensions": {"design-dna": {"textTransform": "uppercase" if st["case"] == "UPPER" else "none",
                                           "fontStyle": "italic" if st["italic"] else "normal",
                                           "letterSpacingEm": st["ls_value"]}},
        })
    return t


def combined(s: dict, d: DTCG) -> dict:
    t = primitives(s, d)
    t.update(typography(s, d))
    light, dark = s["color"]["semantic"]["light"], s["color"]["semantic"]["dark"]
    for name, ref in light.items():
        _set(t, ["color"] + name.split("."), {"$type": "color", "$value": _ref(ref),
                                              "$extensions": {"mode": {"light": _ref(ref), "dark": _ref(dark[name])}}})
    t["$description"] = f"{s['name']} — generated by design-dna. Semantic colors carry light/dark values in $extensions.mode."
    return t


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

def css_var(ref: str) -> str:
    group, key = ref.split(".")
    return f"var(--color-{group}-{key})"


def _rem(px: float) -> str:
    return f"{px / 16:g}rem"


def css(s: dict) -> str:
    col, ty, lay, shape = s["color"], s["typography"], s["layout"], s["shape"]
    out = [f"/* {s['name']} — design tokens generated by design-dna. */", "", ":root {"]
    for group, ramp in col["ramps"].items():
        out += [f"  --color-{group}-{step}: {hx};" for step, hx in ramp.items()]
    out += [f"  --color-base-{k}: {v};" for k, v in col["base"].items()]
    out.append("")
    out += [f"  --font-{r}: {f['stack']};" for r, f in ty["families"].items()]
    out += [f"  --font-weight-{k}: {v};" for k, v in ty["weights"].items()]
    out += [f"  --text-{k}: {_rem(v)};" for k, v in ty["sizes"].items()]
    out += [f"  --leading-{k}: {v};" for k, v in ty["line_height"].items()]
    out += [f"  --tracking-{k}: {v:g}em;" for k, v in ty["tracking"].items()]
    out.append("")
    out += [f"  --space-{k}: {_rem(v)};" for k, v in s["space"].items()]
    out += [f"  --radius-{k}: {'9999px' if v >= 9999 else f'{v}px'};" for k, v in shape["radius"].items()]
    out += [f"  --border-width-{k}: {v}px;" for k, v in shape["border_width"].items()]
    for k, sh in s["shadow"].items():
        out.append(f"  --shadow-{k}: {sh['x']}px {sh['y']}px {sh['blur']}px {sh['spread']}px {_rgba(sh['color'], sh['alpha'])};")
    out += [f"  --duration-{k}: {v}ms;" for k, v in s["motion"]["duration"].items()]
    out += [f"  --ease-{k}: cubic-bezier({', '.join(f'{x:g}' for x in v)});" for k, v in s["motion"]["easing"].items()]
    out.append("")
    out += [f"  --layout-margin: {lay['margin']}px;", f"  --layout-margin-mobile: {lay['margin_mobile']}px;",
            f"  --layout-gutter: {lay['gutter']}px;", f"  --layout-max-width: {lay['max_width']}px;",
            f"  --layout-measure: {lay['measure']}ch;", f"  --layout-section-gap: {lay['section_gap']}px;",
            f"  --layout-stack-gap: {lay['stack_gap']}px;", f"  --layout-columns: {lay['columns']};", "}", ""]

    def block(selector: str, mode: str, indent: str = "") -> list[str]:
        lines = [f"{indent}{selector} {{", f"{indent}  color-scheme: {mode};"]
        for name, ref in col["semantic"][mode].items():
            lines.append(f"{indent}  --color-{name.replace('.', '-')}: {css_var(ref)};")
        lines.append(f"{indent}}}")
        return lines

    out += ["/* Semantic colors — light is the default */"]
    out += block(':root, [data-theme="light"]', "light")
    out += ["", "@media (prefers-color-scheme: dark) {"]
    out += block(':root:not([data-theme="light"])', "dark", "  ")
    out += ["}", ""]
    out += block(':root[data-theme="dark"], [data-theme="dark"]', "dark")
    out += ["", "/* Text styles */"]
    for st in ty["styles"]:
        size = f"var(--text-{st['size']})" if st.get("size") else _rem(st["px"])
        out.append(f".text-{st['name']} {{ font-family: var(--font-{st['family']}); font-size: {size}; "
                   f"font-weight: var(--font-weight-{st['weight']}); line-height: var(--leading-{st['lh']}); "
                   f"letter-spacing: var(--tracking-{st['ls']});"
                   + (" text-transform: uppercase;" if st["case"] == "UPPER" else "")
                   + (" font-style: italic;" if st["italic"] else "") + " }")
    return "\n".join(out) + "\n"
