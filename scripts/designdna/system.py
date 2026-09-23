"""Resolve a learned profile (+ overrides + brief locks) into concrete design-system decisions.

Precedence for every decision: overrides.json  >  brief locks  >  declared values  >  learned  >  default.
Every decision records where it came from, so the docs can show provenance.
"""
from __future__ import annotations

import math
import re

from . import color as C
from . import fonts as F

STATUS_HUES = {"success": (150, 0.62), "warning": (80, 0.78), "danger": (27, 0.58), "info": (250, 0.60)}
RADIUS = {
    "sharp":  {"none": 0, "sm": 0, "md": 0, "lg": 2, "xl": 4, "full": 9999},
    "subtle": {"none": 0, "sm": 2, "md": 4, "lg": 6, "xl": 8, "full": 9999},
    "soft":   {"none": 0, "sm": 4, "md": 8, "lg": 12, "xl": 16, "full": 9999},
    "round":  {"none": 0, "sm": 8, "md": 12, "lg": 20, "xl": 28, "full": 9999},
    "pill":   {"none": 0, "sm": 8, "md": 16, "lg": 24, "xl": 32, "full": 9999},
}
SHADOW_ALPHA = {"flat": (0.05, 0.06, 0.08), "subtle": (0.06, 0.10, 0.14), "layered": (0.10, 0.16, 0.24)}
SPACE = {"0": 0, "0-5": 2, "1": 4, "1-5": 6, "2": 8, "3": 12, "4": 16, "5": 20, "6": 24, "8": 32, "10": 40,
         "12": 48, "16": 64, "20": 80, "24": 96, "32": 128}
UP_NAMES = ["lg", "xl", "2xl", "3xl", "4xl", "5xl", "6xl", "7xl"]
EDITORIAL = {"editorial", "minimal", "minimalist", "classic", "restrained", "formal", "refined", "understated",
             "elegant", "serious", "architectural", "brutalist", "austere", "literary"}
PLAYFUL = {"playful", "friendly", "warm", "approachable", "fun", "youthful", "soft", "casual", "organic"}
CALM = {"calm", "serene", "quiet", "luxurious", "restrained", "contemplative", "refined", "elegant"}
ENERGETIC = {"energetic", "bold", "dynamic", "playful", "vibrant", "loud", "punchy"}


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "design-system"


def _get(d, *path, default=None):
    for k in path:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d if d not in (None, "") else default


def _valid_hex(v) -> str | None:
    if isinstance(v, str) and re.fullmatch(r"#?[0-9A-Fa-f]{6}", v.strip()):
        return "#" + v.strip().lstrip("#").upper()
    return None


class Resolver:
    """Tracks provenance while picking values in precedence order."""

    def __init__(self):
        self.provenance: dict[str, str] = {}

    def first(self, key: str, *candidates):
        for value, why in candidates:
            if value is not None and value is not False and value not in ("", [], {}):
                self.provenance[key] = why
                return value
        return None


# ---------------------------------------------------------------------------
# Color
# ---------------------------------------------------------------------------

def _on_color(bg: str, light: str, dark: str) -> tuple[str, float]:
    a, b = C.contrast(light, bg), C.contrast(dark, bg)
    return ("light", a) if a >= 4.5 or a >= b else ("dark", b)


def _action_step(ramp: dict, start: int, light: str, dark: str, prefer_darker: bool) -> int:
    steps = list(C.STEPS)
    i0 = steps.index(start)
    order = sorted(range(len(steps)), key=lambda i: (abs(i - i0), (i < i0) if prefer_darker else (i > i0)))
    for i in order:
        s = steps[i]
        if max(C.contrast(light, ramp[s]), C.contrast(dark, ramp[s])) >= 4.5:
            return s
    return start


def _first_step(ramp: dict, candidates, bg: str, minimum: float) -> int:
    for s in candidates:
        if C.contrast(ramp[s], bg) >= minimum:
            return s
    return candidates[-1]


def resolve_color(profile: dict, ov: dict, locks: dict, R: Resolver) -> dict:
    col = profile.get("color", {})
    accents = col.get("accents", [])
    declared = [d for d in col.get("declared", []) if d.get("weight", 0) >= 1.0]

    def declared_for(*hints):
        for d in declared:
            if d.get("role_hint") in hints and C.hex_to_oklch(d["hex"])[1] >= 0.03:
                return d
        return None

    dp = declared_for("primary")
    top = accents[0] if accents else None
    any_declared = next((d for d in declared if C.hex_to_oklch(d["hex"])[1] >= 0.05), None)
    primary = R.first(
        "color.primary",
        (_valid_hex(_get(ov, "color", "primary")), "override"),
        (_valid_hex(_get(locks, "colors", "primary")), "brief lock"),
        (dp and dp["hex"], f"declared as primary in {', '.join(dp['kinds']) if dp else ''} ({dp['count'] if dp else 0}×)"),
        (top and top["hex"], f"learned: top accent, {top['share']:.1%} of color mass, in {top['support']:.0%} of sources" if top else ""),
        (any_declared and any_declared["hex"], "declared color (no role stated)"),
        ("#3B5BDB", "default — no chromatic evidence in corpus"),
    )
    pL, pC, ph = C.hex_to_oklch(primary)

    def distinct(hx):  # the accent must not collapse onto the primary
        return hx if hx and C.delta_e(hx, primary) >= 0.05 else None

    da = next((d for d in declared if d.get("role_hint") in ("accent", "secondary") and distinct(d["hex"])
               and C.hex_to_oklch(d["hex"])[1] >= 0.03), None)
    learned_acc = next((a for a in accents[1:] + accents[:1]
                        if distinct(a["hex"]) and C.hue_distance(a["oklch"][2], ph) >= 30 and a["oklch"][1] >= 0.06), None)
    accent = R.first(
        "color.accent",
        (_valid_hex(_get(ov, "color", "accent")), "override"),
        (distinct(_valid_hex(_get(locks, "colors", "accent") or _get(locks, "colors", "secondary"))), "brief lock"),
        (da and da["hex"], f"declared as accent/secondary in {', '.join(da['kinds'])}" if da else ""),
        (learned_acc and learned_acc["hex"],
         f"learned: second accent, {learned_acc['share']:.1%} of color mass" if learned_acc else ""),
        (C.oklch_to_hex(min(0.7, max(0.5, pL)), max(0.08, pC * 0.8), (ph + 150) % 360),
         "derived: split-complement of primary (corpus has no second accent)"),
    )

    tint = col.get("neutral_tint", {"hue": 0, "chroma": 0})
    nhex = _valid_hex(_get(ov, "color", "neutral"))
    if nhex:
        _, nC, nh = C.hex_to_oklch(nhex)
        R.provenance["color.neutral"] = "override"
    else:
        nC, nh = tint.get("chroma", 0), tint.get("hue", 0)
        R.provenance["color.neutral"] = f"learned neutral tint (hue {nh:.0f}°, chroma {nC:.3f})"
    neutral = C.neutral_ramp(nh, nC)

    paper_l = col.get("paper", [])
    ink_l = col.get("ink", [])
    paper = R.first(
        "color.paper",
        (_valid_hex(_get(ov, "color", "background")), "override"),
        (_valid_hex(_get(locks, "colors", "background")), "brief lock"),
        (paper_l and C.hex_to_oklch(paper_l[0]["hex"])[0] >= 0.93 and paper_l[0]["hex"],
         f"learned paper color ({paper_l[0]['name']})" if paper_l else ""),
        ("#FFFFFF", "default white"),
    )
    ink = R.first(
        "color.ink",
        (_valid_hex(_get(ov, "color", "text")), "override"),
        (_valid_hex(_get(locks, "colors", "text")), "brief lock"),
        (ink_l and C.hex_to_oklch(ink_l[0]["hex"])[0] <= 0.3 and ink_l[0]["hex"],
         f"learned ink color ({ink_l[0]['name']})" if ink_l else ""),
        (neutral[900], "neutral 900"),
    )
    if C.contrast(ink, paper) < 7:
        ink = neutral[950]
        R.provenance["color.ink"] += " → darkened to neutral 950 for AAA body contrast"
    surface = "#FFFFFF" if C.hex_to_oklch(paper)[0] < 0.985 else neutral[50]

    ramps: dict[str, dict] = {}
    anchors: dict[str, int] = {}
    ramps["brand"], anchors["brand"] = C.ramp(primary)
    ramps["accent"], anchors["accent"] = C.ramp(accent)
    ramps["neutral"] = neutral
    status_src = {}
    base_c = min(0.17, max(0.11, pC))
    for name, (hue, L) in STATUS_HUES.items():
        match = next((a for a in accents if C.hue_distance(a["oklch"][2], hue) <= 18 and a["oklch"][1] >= 0.08
                      and C.delta_e(a["hex"], primary) > 0.05), None)
        if match:
            ramps[name], anchors[name] = C.ramp(match["hex"])
            status_src[name] = f"learned ({match['name']} {match['hex']})"
        else:
            ramps[name], anchors[name] = C.ramp(C.oklch_to_hex(L, base_c, hue))
            status_src[name] = "generated, chroma matched to primary"
    R.provenance["color.status"] = "; ".join(f"{k}: {v}" for k, v in status_src.items())
    base = {"white": "#FFFFFF", "black": "#000000", "paper": paper, "ink": ink, "surface": surface}

    def val(ref: str) -> str:
        group, key = ref.split(".")
        return base[key] if group == "base" else ramps[group][int(key)]

    white, near_black = "base.white", "neutral.950"

    def action(group: str, mode: str):
        r = ramps[group]
        if mode == "light":
            s = _action_step(r, anchors[group], base["white"], neutral[950], prefer_darker=True)
            hover = C.STEPS[min(len(C.STEPS) - 1, C.STEPS.index(s) + 1)]
            subtle = 100
        else:
            aL = C.hex_to_oklch(r[anchors[group]])[0]
            start = anchors[group] if 0.55 <= aL <= 0.8 else 400
            s = _action_step(r, start, base["white"], neutral[950], prefer_darker=False)
            hover = C.STEPS[max(0, C.STEPS.index(s) - 1)]
            subtle = 900
        on, ratio = _on_color(r[s], base["white"], neutral[950])
        key = f"color.{group_name(group)}.{mode}"
        note = f"step {s}" + (" (anchor)" if s == anchors[group] else f" (anchor {anchors[group]} shifted for AA)")
        white_ratio = C.contrast(base["white"], r[s])
        note += (f"; text on it is {'white' if on == 'light' else 'near-black'} at {ratio:.1f}:1"
                 + (f" (white would be {white_ratio:.1f}:1)" if on == "dark" else ""))
        R.provenance[key] = note
        return {
            f"{group_name(group)}.default": f"{group}.{s}",
            f"{group_name(group)}.hover": f"{group}.{hover}",
            f"{group_name(group)}.subtle": f"{group}.{subtle}",
            f"{group_name(group)}.on": white if on == "light" else near_black,
        }

    def group_name(g):
        return "primary" if g == "brand" else g

    semantic = {"light": {}, "dark": {}}
    L = semantic["light"]
    L.update({"bg.canvas": "base.paper", "bg.surface": "base.surface", "bg.subtle": "neutral.100",
              "bg.muted": "neutral.200", "bg.inverse": "neutral.900",
              "text.default": "base.ink",
              "text.muted": f"neutral.{_first_step(neutral, [600, 700, 800], paper, 4.5)}",
              "text.subtle": f"neutral.{_first_step(neutral, [500, 600, 700], paper, 3.0)}",
              "text.inverse": "neutral.50",
              "text.link": f"brand.{_first_step(ramps['brand'], [s for s in C.STEPS if s >= max(500, anchors['brand'])], paper, 4.5)}",
              "border.default": "neutral.200", "border.strong": "neutral.400", "border.focus": "brand.500"})
    L.update(action("brand", "light"))
    L.update(action("accent", "light"))
    for st in STATUS_HUES:
        L.update({f"{st}.default": f"{st}.600", f"{st}.subtle": f"{st}.100",
                  f"{st}.text": f"{st}.{_first_step(ramps[st], [700, 800, 900], ramps[st][100], 4.5)}"})
    D = semantic["dark"]
    dark_canvas = neutral[950]
    D.update({"bg.canvas": "neutral.950", "bg.surface": "neutral.900", "bg.subtle": "neutral.800",
              "bg.muted": "neutral.700", "bg.inverse": "neutral.50",
              "text.default": "base.paper" if C.hex_to_oklch(paper)[0] >= 0.93 else "neutral.50",
              "text.muted": f"neutral.{_first_step(neutral, [300, 200, 100], dark_canvas, 4.5)}",
              "text.subtle": f"neutral.{_first_step(neutral, [400, 300, 200], dark_canvas, 3.0)}",
              "text.inverse": "neutral.900",
              "text.link": f"brand.{_first_step(ramps['brand'], [300, 200, 100, 50], dark_canvas, 4.5)}",
              "border.default": "neutral.800", "border.strong": "neutral.600", "border.focus": "brand.400"})
    D.update(action("brand", "dark"))
    D.update(action("accent", "dark"))
    for st in STATUS_HUES:
        D.update({f"{st}.default": f"{st}.400", f"{st}.subtle": f"{st}.900",
                  f"{st}.text": f"{st}.{_first_step(ramps[st], [200, 100, 50], ramps[st][900], 4.5)}"})

    pairs = [("text.default", "bg.canvas", 7.0), ("text.default", "bg.surface", 7.0), ("text.muted", "bg.canvas", 4.5),
             ("text.subtle", "bg.canvas", 3.0), ("text.link", "bg.canvas", 4.5), ("primary.on", "primary.default", 4.5),
             ("accent.on", "accent.default", 4.5)] + [(f"{s}.text", f"{s}.subtle", 4.5) for s in STATUS_HUES]
    report = []
    for mode in ("light", "dark"):
        for fg, bg, target in pairs:
            ratio = C.contrast(val(semantic[mode][fg]), val(semantic[mode][bg]))
            report.append({"mode": mode, "fg": fg, "bg": bg, "ratio": round(ratio, 2), "target": target,
                           "pass": ratio >= target, "aa": ratio >= 4.5 or target < 4.5})

    return {"ramps": ramps, "anchors": anchors, "base": base, "semantic": semantic, "contrast": report,
            "primary": primary, "accent": accent, "names": {"primary": C.describe(primary), "accent": C.describe(accent),
                                                              "paper": C.describe(paper), "ink": C.describe(ink)},
            "accent_coverage": col.get("accent_coverage"), "values": {m: {k: val(v) for k, v in semantic[m].items()}
                                                                     for m in semantic}}


# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

def _family(name: str, learned: dict | None) -> dict:
    info = F.classify(name, fallback=(learned or {}).get("category", "sans"))
    if learned and learned.get("family") == name and not info["known"]:
        info["category"] = learned.get("category", info["category"])
        info["substitute"] = learned.get("substitute") or info["substitute"]
    sub = info["substitute"] if info["substitute"] != info["family"] else None
    web = sub or info["family"]
    return {"name": info["family"], "category": info["category"], "substitute": sub, "web": web,
            "stack": F.css_stack(info["family"], info["category"], sub),
            "figma": [x for x in dict.fromkeys([info["family"], web, "Inter"])]}


def resolve_typography(profile: dict, ov: dict, locks: dict, R: Resolver) -> dict:
    t = profile.get("typography", {})
    roles = t.get("roles", {})
    ld, lb, lm = roles.get("display"), roles.get("body"), roles.get("mono")
    display_name = R.first("font.display",
                           (_get(ov, "typography", "display"), "override"),
                           (_get(locks, "fonts", "display"), "brief lock"),
                           (ld and ld["family"], f"learned: dominant display face in {len(ld['sources'])} sources" if ld else ""),
                           (lb and lb["family"], "learned body face (no distinct display face)"),
                           ("Inter", "default"))
    body_name = R.first("font.body",
                        (_get(ov, "typography", "body"), "override"),
                        (_get(locks, "fonts", "body"), "brief lock"),
                        (lb and lb["family"], f"learned: dominant text face in {len(lb['sources'])} sources" if lb else ""),
                        ("Inter", "default"))
    mono_name = R.first("font.mono",
                        (_get(ov, "typography", "mono"), "override"),
                        (_get(locks, "fonts", "mono"), "brief lock"),
                        (lm and lm["family"], "learned mono face"),
                        ("JetBrains Mono", "default"))
    fam = {"display": _family(display_name, ld), "body": _family(body_name, lb), "mono": _family(mono_name, lm)}

    body_w = (lb or {}).get("weight", 400) if (lb and lb["family"] == body_name) else 400
    body_w = body_w if 300 <= body_w <= 500 else 400
    disp_w = (ld or {}).get("weight", 700) if (ld and ld["family"] == display_name) else 700
    weights = {"regular": body_w, "medium": 500, "semibold": 600, "bold": 700, "display": int(disp_w)}

    ratio = R.first("font.scale", (_get(ov, "typography", "ratio"), "override"),
                    (_get(t, "scale", "ratio"), f"learned: heading levels {(_get(t, 'scale', 'levels') or [])[:5]} "
                                                 f"fit {_get(t, 'scale', 'ratio_raw')} → {_get(t, 'scale', 'ratio_name')}"),
                    (1.25, "default major third"))
    ratio = float(ratio)
    base = R.first("font.base", (_get(ov, "typography", "base_px"), "override"),
                   (18 if fam["body"]["category"] in ("serif", "slab") else None, "serif text face reads best at 18px on screen"),
                   (16, "default"))
    base = int(base)
    max_ratio = min(7.0, max(3.0, float(_get(t, "scale", "max_display_ratio") or 4.0)))
    limit = min(base * max_ratio, 128)
    up = []
    k = 1
    while len(up) < 8:
        v = base * ratio ** k
        if v > limit and len(up) >= 4:
            break
        up.append(max(round(v), (up[-1] + 2) if up else base + 1))
        k += 1
    sizes = {"xs": max(11, round(base / ratio ** 2)), "sm": max(13, round(base / ratio)), "base": base}
    if sizes["xs"] >= sizes["sm"]:
        sizes["xs"] = sizes["sm"] - 1
    for name, v in zip(UP_NAMES, up):
        sizes[name] = v
    up_names = UP_NAMES[:len(up)]

    lb_print = _get(t, "leading", "body")
    ld_print = _get(t, "leading", "display")
    lh = {"body": round(min(1.75, max(1.4, (lb_print or 1.25) * 1.2)) * 20) / 20,
          "display": round(min(1.25, max(1.0, ld_print or 1.1)) * 20) / 20}
    lh["heading"] = round(min(1.35, max(1.15, (lh["body"] + lh["display"]) / 2)) * 20) / 20
    upper_h = (_get(t, "case", "headings_uppercase") or 0) >= 0.5
    upper_l = (_get(t, "case", "labels_uppercase") or 0) >= 0.4
    dcat = fam["display"]["category"]
    tracking = {"display": 0.04 if upper_h else (-0.02 if dcat in ("sans", "display") else -0.01),
                "heading": 0.02 if upper_h else (-0.01 if dcat in ("sans", "display") else 0.0),
                "body": 0.0, "label": 0.08 if upper_l else 0.01}

    def sz(n):
        return sizes[n]

    top = up_names[::-1]
    h2 = (top[3], None) if len(top) >= 5 else (None, round(math.sqrt(sz(up_names[0]) * sz(up_names[1]))))
    h3 = (top[4], None) if len(top) >= 6 else (up_names[0], None)
    serif_display = dcat in ("serif", "slab")
    case_d = "UPPER" if upper_h else "ORIGINAL"
    styles = [
        {"name": "display-xl", "family": "display", "size": top[0], "weight": "display", "lh": "display", "ls": "display", "case": case_d},
        {"name": "display-lg", "family": "display", "size": top[1], "weight": "display", "lh": "display", "ls": "display", "case": case_d},
        {"name": "heading-1", "family": "display", "size": top[2], "weight": "display", "lh": "heading", "ls": "heading", "case": case_d},
        {"name": "heading-2", "family": "display", "size": h2[0], "px": h2[1], "weight": "display", "lh": "heading", "ls": "heading", "case": case_d},
        {"name": "heading-3", "family": "body" if not serif_display else "display", "size": h3[0], "weight": "semibold", "lh": "heading", "ls": "body", "case": "ORIGINAL"},
        {"name": "body-lg", "family": "body", "size": "lg", "weight": "regular", "lh": "body", "ls": "body", "case": "ORIGINAL"},
        {"name": "body", "family": "body", "size": "base", "weight": "regular", "lh": "body", "ls": "body", "case": "ORIGINAL"},
        {"name": "body-sm", "family": "body", "size": "sm", "weight": "regular", "lh": "body", "ls": "body", "case": "ORIGINAL"},
        {"name": "label", "family": "body", "size": "sm", "weight": "semibold", "lh": "heading", "ls": "label", "case": "UPPER" if upper_l else "ORIGINAL"},
        {"name": "caption", "family": "body", "size": "xs", "weight": "regular", "lh": "heading", "ls": "body", "case": "ORIGINAL"},
        {"name": "quote", "family": "display", "size": up_names[1], "weight": "regular" if serif_display else "display", "lh": "heading", "ls": "heading", "case": "ORIGINAL", "italic": serif_display},
        {"name": "code", "family": "mono", "size": "sm", "weight": "regular", "lh": "body", "ls": "body", "case": "ORIGINAL"},
    ]
    for s in styles:
        s["px"] = s.get("px") or sizes[s["size"]]
        s["weight_value"] = weights[s["weight"]]
        s["lh_value"] = lh[s["lh"]]
        s["ls_value"] = tracking[s["ls"]]
        s.setdefault("italic", False)
    return {"families": fam, "weights": weights, "ratio": ratio, "base": base, "sizes": sizes, "line_height": lh,
            "tracking": tracking, "styles": styles, "declared": t.get("declared", []),
            "print": {"leading_body": lb_print, "leading_display": ld_print, "max_display_ratio": _get(t, "scale", "max_display_ratio"),
                      "measure_chars": t.get("measure_chars"), "levels": _get(t, "scale", "levels")}}


# ---------------------------------------------------------------------------
# Space, layout, shape, motion
# ---------------------------------------------------------------------------

def resolve_layout(profile: dict, ov: dict, R: Resolver) -> dict:
    lay = profile.get("layout", {})
    q = profile.get("qualitative", {})
    ws_vote = _get(q, "decided", "whitespace")
    ws_vote = ws_vote if ws_vote in ("airy", "balanced", "dense") else None
    density = R.first("layout.density", (ov.get("density"), "override"),
                      (ws_vote, "visual review consensus"),
                      (lay.get("density"), f"learned: pages are {lay.get('whitespace') or 0:.0%} empty on average"),
                      ("balanced", "default"))
    margins = lay.get("margins") or {}
    side = [v for v in (margins.get("left"), margins.get("right")) if v]
    margin_px = round(min(160, max(24, (sum(side) / len(side)) * 1440)) / 8) * 8 if side else 64
    gutter_px = round(min(48, max(16, (lay.get("gutter_ratio") or 0.0167) * 1440)) / 4) * 4
    measure = profile.get("typography", {}).get("measure_chars")
    measure = int(min(80, max(45, measure * 1.1))) if measure else 66
    R.provenance["layout.margin"] = (f"learned: print margins ≈ {sum(side) / len(side):.1%} of page width" if side else "default")
    R.provenance["layout.measure"] = (f"learned: ~{profile['typography']['measure_chars']:.0f} chars per body line in print"
                                      if profile.get("typography", {}).get("measure_chars") else "default 66ch")
    return {
        "density": density,
        "section_gap": {"airy": 128, "balanced": 96, "dense": 64}[density],
        "stack_gap": {"airy": 32, "balanced": 24, "dense": 16}[density],
        "margin": margin_px, "margin_mobile": {"airy": 24, "balanced": 20, "dense": 16}[density],
        "gutter": gutter_px, "measure": measure, "max_width": 1200, "columns": 12,
        "print_columns": lay.get("columns"), "imagery": lay.get("imagery"), "image_coverage": lay.get("image_coverage"),
        "whitespace": lay.get("whitespace"),
    }


def _mood_words(profile) -> set[str]:
    return {m["word"] for m in _get(profile, "qualitative", "mood", default=[])[:8]}


def resolve_shape(profile: dict, ov: dict, R: Resolver) -> dict:
    decided = _get(profile, "qualitative", "decided", default={})
    mood = _mood_words(profile)
    default_corners = "subtle" if mood & EDITORIAL else "round" if mood & PLAYFUL else "soft"
    corners = R.first("shape.corners", (_get(ov, "shape", "corners"), "override"),
                      (decided.get("corners") if decided.get("corners") in RADIUS else None, "visual review consensus"),
                      (default_corners, f"inferred from mood ({', '.join(sorted(mood)) or 'none recorded'})"))
    elevation = R.first("shape.elevation", (_get(ov, "shape", "elevation"), "override"),
                        (decided.get("elevation") if decided.get("elevation") in SHADOW_ALPHA else None, "visual review consensus"),
                        ("flat" if mood & EDITORIAL else "subtle", "inferred from mood"))
    borders = R.first("shape.borders", (_get(ov, "shape", "borders"), "override"),
                      (decided.get("borders"), "visual review consensus"), ("hairline", "default"))
    radius = dict(RADIUS.get(corners, RADIUS["soft"]))
    radius["control"] = 9999 if corners == "pill" else radius["md"]
    return {"corners": corners, "elevation": elevation, "borders": borders, "radius": radius,
            "border_width": {"hairline": 1, "default": 2 if borders == "bold" else 1, "strong": 2 if borders != "bold" else 3}}


def resolve_shadows(ink: str, elevation: str) -> dict:
    a1, a2, a3 = SHADOW_ALPHA.get(elevation, SHADOW_ALPHA["subtle"])
    return {"sm": {"x": 0, "y": 1, "blur": 2, "spread": 0, "color": ink, "alpha": a1},
            "md": {"x": 0, "y": 4, "blur": 12, "spread": -2, "color": ink, "alpha": a2},
            "lg": {"x": 0, "y": 12, "blur": 32, "spread": -8, "color": ink, "alpha": a3}}


def resolve_motion(profile: dict) -> dict:
    mood = _mood_words(profile)
    scale = 1.2 if mood & CALM else 0.8 if mood & ENERGETIC else 1.0
    return {"duration": {"fast": round(120 * scale), "base": round(200 * scale), "slow": round(320 * scale)},
            "easing": {"standard": [0.2, 0, 0, 1], "enter": [0, 0, 0, 1], "exit": [0.3, 0, 1, 1]}}


# ---------------------------------------------------------------------------
# Guidance (principles, voice, do/don't)
# ---------------------------------------------------------------------------

def resolve_guidance(profile: dict, sysd: dict) -> dict:
    q = profile.get("qualitative", {})
    principles = [{"text": p["text"], "sources": len(p["sources"]), "origin": "observed"} for p in q.get("principles", [])]
    t, lay, col = sysd["typography"], sysd["layout"], sysd["color"]
    derived = []
    mdr = t["print"].get("max_display_ratio")
    if mdr and mdr >= 3:
        derived.append(f"Make hierarchy obvious: display type runs up to {mdr:.1f}× the body size in the corpus.")
    if lay.get("whitespace") and lay["whitespace"] >= 0.55:
        derived.append(f"Let the canvas breathe: on average {lay['whitespace']:.0%} of each page is left empty.")
    cov = col.get("accent_coverage")
    if cov is not None and cov < 0.12:
        derived.append(f"Use {col['names']['primary']} sparingly: chromatic color covers only ~{cov:.0%} of the corpus. Neutrals carry the layout.")
    elif cov is not None and cov >= 0.3:
        derived.append(f"Color is structural, not decorative: ~{cov:.0%} of the corpus is chromatic.")
    if lay.get("imagery") == "image-led":
        derived.append(f"Lead with imagery: pictures fill ~{lay['image_coverage']:.0%} of page area.")
    elif lay.get("imagery") == "type-led":
        derived.append("Typography does the heavy lifting; imagery is occasional.")
    derived.append(f"Hold body text to a ~{lay['measure']}-character measure.")
    principles += [{"text": d, "sources": None, "origin": "metrics"} for d in derived]
    notes = q.get("notes", {})
    dos = [x["text"] for x in notes.get("dos", [])]
    donts = [x["text"] for x in notes.get("donts", [])]
    donts.append(f"Don't introduce new hues. The palette is {col['names']['primary']} + {col['names']['accent']} + tinted neutrals.")
    if t["families"]["display"]["name"] != t["families"]["body"]["name"]:
        dos.append(f"Pair {t['families']['display']['name']} (display) with {t['families']['body']['name']} (text). Don't swap their roles.")
    return {"principles": principles, "mood": [m["word"] for m in q.get("mood", [])],
            "voice": [v["word"] for v in q.get("voice", [])], "phrases": [p["text"] for p in notes.get("phrases", [])][:6],
            "dos": dos[:12], "donts": donts[:12], "imagery": notes.get("imagery", [])[:6],
            "components_seen": q.get("components_seen", {}), "briefs": q.get("briefs", []),
            "summaries": q.get("summaries", []), "typography_notes": [x["text"] for x in notes.get("typography_notes", [])][:8],
            "color_notes": [x["text"] for x in notes.get("color_notes", [])][:8],
            "composition": [x["text"] for x in notes.get("composition", [])][:6]}


def build_system(profile: dict, overrides: dict | None = None, name: str | None = None) -> dict:
    ov = overrides or {}
    locks = _get(profile, "qualitative", "locks", default={}) or {}
    R = Resolver()
    sys_name = ov.get("name") or name or profile.get("name") or "Design DNA"
    color = resolve_color(profile, ov, locks, R)
    typography = resolve_typography(profile, ov, locks, R)
    layout = resolve_layout(profile, ov, R)
    shape = resolve_shape(profile, ov, R)
    sysd = {
        "name": sys_name, "slug": slugify(sys_name), "generated_at": profile.get("generated_at"),
        "color": color, "typography": typography, "space": dict(SPACE), "layout": layout, "shape": shape,
        "shadow": resolve_shadows(color["base"]["ink"], shape["elevation"]), "motion": resolve_motion(profile),
        "corpus": profile.get("corpus", {}), "confidence": profile.get("confidence", {}),
        "lock_conflicts": _get(profile, "qualitative", "lock_conflicts", default=[]),
    }
    sysd["guidance"] = resolve_guidance(profile, sysd)
    sysd["provenance"] = R.provenance
    return sysd
