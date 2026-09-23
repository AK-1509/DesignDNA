"""Aggregate every source in the corpus into one weighted design profile.

Learning is evidence accumulation: each source contributes observations (colors,
type sizes, fonts, layout metrics, qualitative notes) weighted by its role and
user weight. Consistent signals across many sources win; one-offs fade. The
profile is re-derived from scratch on every run, so adding or removing sources
(or editing observations) is always reflected.
"""
from __future__ import annotations

import math
import re
import shutil
from collections import Counter, defaultdict

import numpy as np

from . import color as C
from . import fonts as F
from .workspace import Workspace, now, read_json, write_json

# How much each role counts, per kind of evidence.
ROLE_WEIGHTS = {
    "brief":     {"visual": 0.3, "declared": 3.0, "type": 0.4, "qual": 1.2},
    "magazine":  {"visual": 1.0, "declared": 0.3, "type": 1.0, "qual": 1.0},
    "portfolio": {"visual": 1.2, "declared": 0.6, "type": 1.0, "qual": 1.1},
    "report":    {"visual": 0.9, "declared": 1.0, "type": 0.9, "qual": 0.9},
    "reference": {"visual": 1.0, "declared": 1.0, "type": 1.0, "qual": 1.0},
}
STANDARD_RATIOS = {1.067: "minor second", 1.125: "major second", 1.2: "minor third", 1.25: "major third",
                   1.333: "perfect fourth", 1.414: "augmented fourth", 1.5: "perfect fifth", 1.618: "golden ratio"}
THEME_SLOT_ROLE = {"accent1": "primary", "accent2": "accent", "accent3": "accent", "dk1": "text", "dk2": "text",
                   "lt1": "background", "lt2": "background", "hlink": "link"}


def _rw(src: dict) -> dict:
    return ROLE_WEIGHTS.get(src.get("role", "reference"), ROLE_WEIGHTS["reference"])


def _uw(src: dict) -> float:
    try:
        return max(0.0, float(src.get("weight", 1.0)))
    except (TypeError, ValueError):
        return 1.0


def wmedian(pairs):
    pairs = sorted((v, w) for v, w in pairs if v is not None and w > 0)
    if not pairs:
        return None
    total = sum(w for _, w in pairs)
    acc = 0.0
    for v, w in pairs:
        acc += w
        if acc >= total / 2:
            return round(float(v), 4)
    return round(float(pairs[-1][0]), 4)


def wmean(pairs):
    pairs = [(v, w) for v, w in pairs if v is not None and w > 0]
    if not pairs:
        return None
    return round(sum(v * w for v, w in pairs) / sum(w for _, w in pairs), 4)


# ---------------------------------------------------------------------------
# Color
# ---------------------------------------------------------------------------

def _cluster(evidence, thr=0.045):
    evidence = sorted(evidence, key=lambda e: -e[1])
    clusters = []
    for lab, w, sid, channel in evidence:
        if w <= 0:
            continue
        best, bd = None, thr
        for c in clusters:
            d = float(np.linalg.norm(c["lab"] - lab))
            if d < bd:
                best, bd = c, d
        if best is None:
            clusters.append({"lab": np.array(lab, dtype=float), "w": w, "sources": {sid}, "channels": Counter({channel: w})})
        else:
            best["lab"] = (best["lab"] * best["w"] + lab * w) / (best["w"] + w)
            best["w"] += w
            best["sources"].add(sid)
            best["channels"][channel] += w
    return clusters


def learn_color(sources: list[dict]) -> dict:
    evidence, declared = [], []
    color_sources = set()
    for s in sources:
        a, sid, rw, uw = s["analysis"], s["id"], _rw(s), _uw(s)
        col = a.get("color") or {}
        chans = [(n, col.get(k), sh) for n, k, sh in (("page", "page_palette", 0.55), ("vector", "vector_colors", 0.30),
                                                        ("text", "text_colors", 0.15)) if col.get(k)]
        tot = sum(sh for _, _, sh in chans)
        for name, lst, sh in chans:
            lw = sum(x["weight"] for x in lst) or 1
            for x in lst:
                evidence.append((C.hex_to_oklab(x["hex"]), rw["visual"] * uw * sh / tot * x["weight"] / lw, sid, name))
            color_sources.add(sid)
        theme = a.get("theme")
        if theme:
            f = 0.1 if theme.get("is_office_default") else 1.0
            for slot, hx in (theme.get("colors") or {}).items():
                declared.append({"hex": hx, "w": rw["declared"] * uw * f * (1.5 if slot == "accent1" else 1.0),
                                 "hint": THEME_SLOT_ROLE.get(slot), "sid": sid, "context": f"theme slot {slot}",
                                 "kind": "theme"})
        text = a.get("text") or {}
        for d in text.get("declared_colors") or []:
            declared.append({"hex": d["hex"], "w": rw["declared"] * uw * (0.6 if d.get("approx") else 1.0),
                             "hint": d.get("role_hint"), "sid": sid, "context": d.get("context", ""), "kind": d.get("kind")})
        for v in text.get("css_variables") or []:
            hint = next((r for r, pat in (("primary", "primary|brand"), ("accent", "accent|secondary"),
                                          ("background", "bg|background|surface"), ("text", "text|fg|ink"))
                         if re.search(pat, v["name"])), None)
            declared.append({"hex": v["hex"], "w": rw["declared"] * uw * 0.8, "hint": hint, "sid": sid,
                             "context": v["name"], "kind": "css-variable"})

    # declared colors also count as visual evidence, capped per source
    per_src = defaultdict(float)
    caps = {s["id"]: 0.6 * _rw(s)["declared"] * _uw(s) for s in sources}
    for d in declared:
        w = min(d["w"] * 0.2, max(0.0, caps[d["sid"]] - per_src[d["sid"]]))
        per_src[d["sid"]] += w
        evidence.append((C.hex_to_oklab(d["hex"]), w, d["sid"], "declared"))
        color_sources.add(d["sid"])

    clusters = _cluster(evidence)
    total = sum(c["w"] for c in clusters) or 1
    n_src = max(1, len(color_sources))
    paper, ink, mids, accents = [], [], [], []
    for c in clusters:
        L, Cc, h = C.oklab_to_oklch(c["lab"])
        item = {"hex": C.oklab_to_hex(c["lab"]), "share": round(c["w"] / total, 4),
                "support": round(len(c["sources"]) / n_src, 3), "sources": sorted(c["sources"]),
                "oklch": [round(L, 3), round(Cc, 3), round(h, 1)], "name": C.describe(C.oklab_to_hex(c["lab"])),
                "channels": {k: round(v / c["w"], 2) for k, v in c["channels"].items()}}
        if Cc < 0.035 or (L > 0.92 and Cc < 0.05):
            (paper if L >= 0.9 else ink if L <= 0.32 else mids).append(item)
        else:
            item["score"] = round(item["share"] * (0.5 + item["support"]) * min(1.0, Cc / 0.1), 5)
            accents.append(item)
    for lst in (paper, ink, mids):
        lst.sort(key=lambda x: -x["share"])
    accents.sort(key=lambda x: -x["score"])

    # neutral tint = weighted hue/chroma of all neutrals
    neutrals = paper + ink + mids
    if neutrals:
        a = sum(C.hex_to_oklab(n["hex"])[1] * n["share"] for n in neutrals)
        b = sum(C.hex_to_oklab(n["hex"])[2] * n["share"] for n in neutrals)
        s = sum(n["share"] for n in neutrals) or 1
        tint = {"hue": round(math.degrees(math.atan2(b / s, a / s)) % 360, 1), "chroma": round(math.hypot(a / s, b / s), 4)}
    else:
        tint = {"hue": 0.0, "chroma": 0.0}

    # declared colors grouped
    groups: list[dict] = []
    for d in sorted(declared, key=lambda d: -d["w"]):
        g = next((g for g in groups if C.delta_e(g["hex"], d["hex"]) < 0.02), None)
        if g is None:
            g = {"hex": d["hex"], "weight": 0.0, "count": 0, "hints": Counter(), "sources": set(), "contexts": [],
                 "kinds": set()}
            groups.append(g)
        g["weight"] += d["w"]
        g["count"] += 1
        if d["hint"]:
            g["hints"][d["hint"]] += d["w"]
        g["sources"].add(d["sid"])
        g["kinds"].add(d["kind"])
        if d["context"] and len(g["contexts"]) < 3:
            g["contexts"].append(d["context"][:160])
    declared_out = [{"hex": g["hex"], "weight": round(g["weight"], 3), "count": g["count"],
                     "role_hint": g["hints"].most_common(1)[0][0] if g["hints"] else None,
                     "sources": sorted(g["sources"]), "kinds": sorted(k for k in g["kinds"] if k),
                     "contexts": g["contexts"], "name": C.describe(g["hex"])} for g in groups]
    declared_out.sort(key=lambda d: -d["weight"])
    for acc in accents:
        acc["declared"] = any(C.delta_e(acc["hex"], d["hex"]) < 0.05 for d in declared_out)

    top_support = accents[0]["support"] if accents else 0
    return {
        "paper": paper[:4], "ink": ink[:4], "mid_neutrals": mids[:6], "accents": accents[:10],
        "declared": declared_out[:24], "neutral_tint": tint,
        "accent_coverage": round(sum(a["share"] for a in accents), 4),
        "confidence": round(min(1.0, n_src / 5) * (0.5 + 0.5 * top_support), 3),
        "sources": n_src,
    }


# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

def learn_typography(sources: list[dict]) -> dict:
    fam: dict[str, dict] = {}
    heading_ratios, max_ratios, lead_b, lead_d, up_h, up_l, measure = [], [], [], [], [], [], []
    declared = Counter()
    type_sources = 0
    for s in sources:
        a, sid, rw, uw = s["analysis"], s["id"], _rw(s), _uw(s)
        t = a.get("typography") or {}
        theme = a.get("theme") or {}
        default_theme = bool(theme.get("is_office_default"))
        tw = rw["type"] * uw * (0.1 if default_theme else 1.0)
        fonts = t.get("fonts") or []
        body = t.get("body_size")
        tot = sum(f.get("chars", 0) for f in fonts)
        if fonts and tot:
            type_sources += 1
        for f in fonts:
            e = fam.setdefault(f["family"], {"family": f["family"], "category": f.get("category", "sans"),
                                             "substitute": f.get("substitute"), "known": f.get("known", False),
                                             "total": 0.0, "body": 0.0, "display": 0.0, "small": 0.0,
                                             "w_body": Counter(), "w_display": Counter(), "italic": 0.0,
                                             "sources": set()})
            share = f.get("chars", 0) / tot * tw if tot else 0
            e["total"] += share
            e["sources"].add(sid)
            sizes = f.get("sizes") or {}
            stot = sum(sizes.values())
            if body and stot:
                for sz, c in sizes.items():
                    r, w = float(sz) / body, share * c / stot
                    if r >= 1.5:
                        e["display"] += w
                        e["w_display"][f["weight"]] += w
                    elif r >= 1.15:
                        e["display"] += w * 0.5
                        e["w_display"][f["weight"]] += w * 0.5
                    elif r >= 0.85:
                        e["body"] += w
                        e["w_body"][f["weight"]] += w
                    else:
                        e["small"] += w
            else:
                role = f.get("theme_role")
                if role == "display":
                    e["display"] += share
                    e["w_display"][f.get("weight", 700)] += share
                elif role == "body":
                    e["body"] += share
                    e["w_body"][f.get("weight", 400)] += share
                else:
                    e["body"] += share * 0.6
                    e["display"] += share * 0.4
                    e["w_body"][f.get("weight", 400)] += share * 0.6
            if f.get("italic"):
                e["italic"] += share
        sizes = t.get("sizes") or {}
        stot = sum(sizes.values())
        if body and stot:
            for sz, c in sizes.items():
                r = float(sz) / body
                if r >= 1.1:
                    heading_ratios.append((r, tw * c / stot))
        if t.get("max_display_ratio"):
            max_ratios.append((t["max_display_ratio"], tw))
        lead_b.append((t.get("leading_body"), tw))
        lead_d.append((t.get("leading_display"), tw))
        up_h.append((t.get("headings_uppercase"), tw))
        up_l.append((t.get("labels_uppercase"), tw))
        measure.append((t.get("measure_chars"), tw))
        for name, n in ((a.get("text") or {}).get("font_mentions") or {}).items():
            declared[name] += n * rw["declared"] * uw
        for role, name in (theme.get("fonts") or {}).items():
            declared[name] += 2 * rw["declared"] * uw * (0.1 if default_theme else 1.0)

    def pick(key, exclude_mono=True):
        cands = [e for e in fam.values() if not (exclude_mono and e["category"] == "mono")]
        cands.sort(key=lambda e: -e[key])
        return cands

    body_c = pick("body")
    body_c = [e for e in body_c if e["body"] > 0] or pick("total")
    disp_c = [e for e in pick("display") if e["display"] > 0]
    mono_c = sorted((e for e in fam.values() if e["category"] == "mono" and e["total"] > 0.01), key=lambda e: -e["total"])

    def role(cands, key, wkey, default_weight):
        if not cands:
            return None
        e = cands[0]
        weight = e[wkey].most_common(1)[0][0] if e[wkey] else default_weight
        return {"family": e["family"], "category": e["category"], "substitute": e["substitute"], "known": e["known"],
                "weight": int(weight), "score": round(e[key], 4), "sources": sorted(e["sources"]),
                "italic_share": round(e["italic"] / e["total"], 3) if e["total"] else 0,
                "alternatives": [{"family": x["family"], "score": round(x[key], 4)} for x in cands[1:4]]}

    body_role = role(body_c, "body", "w_body", 400)
    disp_role = role(disp_c, "display", "w_display", 700) or body_role
    mono_role = role(mono_c, "total", "w_body", 400)

    # type scale: cluster heading ratios into levels, then fit a geometric progression
    ratio, levels = None, []
    if heading_ratios:
        heading_ratios.sort()
        groups: list[list] = []
        for r, w in heading_ratios:
            if groups and r / groups[-1][-1][0] < 1.08:
                groups[-1].append((r, w))
            else:
                groups.append([(r, w)])
        tw_all = sum(w for _, w in heading_ratios) or 1
        for g in groups:
            gw = sum(w for _, w in g)
            if gw / tw_all >= 0.03:
                levels.append((math.exp(sum(math.log(r) * w for r, w in g) / gw), gw))
        seq = [1.0] + [lv for lv, _ in levels]
        diffs = [math.log(b / a) for a, b in zip(seq, seq[1:]) if b > a]
        if diffs:
            ratio = math.exp(float(np.median(diffs)))
    snapped = min(STANDARD_RATIOS, key=lambda q: abs(math.log(q) - math.log(ratio))) if ratio else 1.25
    snapped = min(max(snapped, 1.125), 1.618)

    return {
        "roles": {"display": disp_role, "body": body_role, "mono": mono_role},
        "families": [{"family": e["family"], "category": e["category"], "substitute": e["substitute"],
                      "share": round(e["total"], 4), "body": round(e["body"], 4), "display": round(e["display"], 4),
                      "sources": len(e["sources"])} for e in sorted(fam.values(), key=lambda e: -e["total"])[:12]],
        "declared": [{"family": k, "weight": round(v, 3), **{kk: vv for kk, vv in F.classify(k).items() if kk != "family"}}
                     for k, v in declared.most_common(8)],
        "scale": {"ratio_raw": round(ratio, 3) if ratio else None, "ratio": snapped,
                  "ratio_name": STANDARD_RATIOS.get(snapped, "custom"),
                  "levels": [round(lv, 3) for lv, _ in levels][:10],
                  "max_display_ratio": wmedian(max_ratios)},
        "leading": {"body": wmedian(lead_b), "display": wmedian(lead_d)},
        "case": {"headings_uppercase": wmean(up_h), "labels_uppercase": wmean(up_l)},
        "measure_chars": wmedian(measure),
        "confidence": round(min(1.0, type_sources / 4) * (1.0 if body_role else 0.3), 3),
        "sources": type_sources,
    }


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def learn_layout(sources: list[dict]) -> dict:
    m = defaultdict(list)
    cols, gut, img, wsp, txt = Counter(), [], [], [], []
    orient = Counter()
    n = 0
    for s in sources:
        lay = (s["analysis"].get("layout") or {})
        if not lay:
            continue
        w = _rw(s)["visual"] * _uw(s)
        n += 1
        for side, v in (lay.get("margins") or {}).items():
            m[side].append((v, w))
        if lay.get("columns"):
            cols[lay["columns"]] += w
        gut.append((lay.get("gutter_ratio"), w))
        img.append((lay.get("image_coverage"), w))
        wsp.append((lay.get("whitespace"), w))
        txt.append((lay.get("text_coverage"), w))
        if lay.get("orientation"):
            orient[lay["orientation"]] += w
    whitespace = wmean(wsp)
    image_cov = wmean(img)
    return {
        "margins": {k: wmedian(v) for k, v in m.items()} or None,
        "columns": cols.most_common(1)[0][0] if cols else None,
        "columns_distribution": dict(cols.most_common()),
        "gutter_ratio": wmedian(gut),
        "image_coverage": image_cov,
        "text_coverage": wmean(txt),
        "whitespace": whitespace,
        "density": None if whitespace is None else "airy" if whitespace >= 0.62 else "dense" if whitespace <= 0.42 else "balanced",
        "imagery": None if image_cov is None else "image-led" if image_cov >= 0.35 else "balanced" if image_cov >= 0.15 else "type-led",
        "orientation": orient.most_common(1)[0][0] if orient else None,
        "sources": n,
    }


# ---------------------------------------------------------------------------
# Qualitative (observations written by the design-analyst agent)
# ---------------------------------------------------------------------------

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def learn_qualitative(sources: list[dict]) -> dict:
    mood, voice, components = Counter(), Counter(), Counter()
    votes = defaultdict(Counter)
    principles: dict[str, dict] = {}
    lists = defaultdict(list)
    briefs, summaries = [], []
    locks: dict[str, dict] = {}
    conflicts = []
    n = 0
    for s in sources:
        o = s.get("observation")
        if not isinstance(o, dict):
            continue
        n += 1
        w = _rw(s)["qual"] * _uw(s) * float(o.get("confidence", 0.7) or 0.7)
        sid = s["id"]
        if o.get("summary"):
            summaries.append({"source": sid, "role": s.get("role"), "summary": o["summary"]})
        for m in o.get("mood") or []:
            mood[str(m).lower().strip()] += w
        for p in o.get("principles") or []:
            k = _norm(str(p))
            if not k:
                continue
            e = principles.setdefault(k, {"text": str(p).strip(), "weight": 0.0, "sources": set()})
            e["weight"] += w
            e["sources"].add(sid)
        comp = o.get("composition") or {}
        for key in ("alignment", "whitespace", "hierarchy_style"):
            if comp.get(key):
                votes[key][str(comp[key]).lower()] += w
        for key in ("grid", "notes"):
            if comp.get(key):
                lists["composition"].append({"source": sid, "text": comp[key]})
        shape = o.get("shape") or {}
        for key in ("corners", "borders", "elevation"):
            if shape.get(key):
                votes[key][str(shape[key]).lower()] += w
        for key in ("typography_notes", "color_notes", "dos", "donts"):
            for item in o.get(key) or []:
                if not any(_norm(x["text"]) == _norm(str(item)) for x in lists[key]):
                    lists[key].append({"source": sid, "text": str(item)})
        img = o.get("imagery") or {}
        if img:
            lists["imagery"].append({"source": sid, **{k: v for k, v in img.items() if v}})
        for c in o.get("components_seen") or []:
            components[str(c).lower().strip()] += 1
        v = o.get("voice") or {}
        for attr in v.get("attributes") or []:
            voice[str(attr).lower().strip()] += w
        for ph in (v.get("sample_phrases") or [])[:5]:
            lists["phrases"].append({"source": sid, "text": ph})
        b = o.get("brief")
        if isinstance(b, dict) and any(b.get(k) for k in ("project", "audience", "goals", "constraints")):
            briefs.append({"source": sid, **{k: b.get(k) for k in ("project", "client", "audience", "goals",
                                                                   "constraints", "deliverables", "tone") if b.get(k)}})
            for group, vals in (b.get("locks") or {}).items():
                if not isinstance(vals, dict):
                    continue
                for key, val in vals.items():
                    if val in (None, ""):
                        continue
                    cur = locks.setdefault(group, {}).get(key)
                    if cur and cur["value"] != val:
                        conflicts.append({"lock": f"{group}.{key}", "values": [cur["value"], val],
                                          "sources": [cur["source"], sid]})
                        if w <= cur["weight"]:
                            continue
                    locks[group][key] = {"value": val, "source": sid, "weight": w}

    prin = sorted(principles.values(), key=lambda e: -(e["weight"] * (1 + 0.5 * (len(e["sources"]) - 1))))
    return {
        "observed_sources": n,
        "mood": [{"word": k, "weight": round(v, 3)} for k, v in mood.most_common(12)],
        "principles": [{"text": e["text"], "weight": round(e["weight"], 3), "sources": sorted(e["sources"])}
                       for e in prin[:14]],
        "votes": {k: dict(v.most_common()) for k, v in votes.items()},
        "decided": {k: v.most_common(1)[0][0] for k, v in votes.items() if v},
        "voice": [{"word": k, "weight": round(v, 3)} for k, v in voice.most_common(10)],
        "components_seen": dict(components.most_common(20)),
        "notes": {k: v[:20] for k, v in lists.items()},
        "briefs": briefs,
        "summaries": summaries,
        "locks": {g: {k: v["value"] for k, v in d.items()} for g, d in locks.items()},
        "lock_sources": {f"{g}.{k}": v["source"] for g, d in locks.items() for k, v in d.items()},
        "lock_conflicts": conflicts,
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def learn(ws: Workspace) -> tuple[dict, list[str]]:
    sources = ws.sources()
    if not sources:
        raise SystemExit("No sources ingested yet. Run: dna.py ingest <files>")
    old = read_json(ws.profile_path)
    roles = Counter(s.get("role", "reference") for s in sources)
    profile = {
        "generated_at": now(),
        "name": ws.config.get("name", "Design DNA"),
        "corpus": {"sources": len(sources), "roles": dict(roles),
                   "observed": sum(1 for s in sources if isinstance(s.get("observation"), dict)),
                   "items": [{"id": s["id"], "name": s.get("name"), "role": s.get("role"), "weight": _uw(s),
                              "kind": s["analysis"].get("kind"), "observed": isinstance(s.get("observation"), dict)}
                             for s in sources]},
        "color": learn_color(sources),
        "typography": learn_typography(sources),
        "layout": learn_layout(sources),
        "qualitative": learn_qualitative(sources),
    }
    q = profile["qualitative"]
    profile["confidence"] = {
        "color": profile["color"]["confidence"],
        "typography": profile["typography"]["confidence"],
        "layout": round(min(1.0, profile["layout"]["sources"] / 4), 3),
        "qualitative": round(q["observed_sources"] / len(sources), 3),
    }
    changes = diff(old, profile) if old else []
    if old:
        hist = ws.root / "history"
        hist.mkdir(exist_ok=True)
        stamp = (old.get("generated_at") or now()).replace(":", "").replace("-", "")
        shutil.copy(ws.profile_path, hist / f"profile-{stamp}.json")
    write_json(ws.profile_path, profile)
    (ws.root / "profile.md").write_text(render_markdown(profile), encoding="utf-8")
    return profile, changes


def _top(p, *path):
    cur = p
    for k in path:
        if isinstance(cur, dict):
            cur = cur.get(k)
        elif isinstance(cur, list) and isinstance(k, int):
            cur = cur[k] if len(cur) > k else None
        else:
            return None
    return cur


def diff(old: dict, new: dict) -> list[str]:
    out = []
    checks = [
        ("top accent", ("color", "accents", 0, "hex")),
        ("paper", ("color", "paper", 0, "hex")),
        ("ink", ("color", "ink", 0, "hex")),
        ("display family", ("typography", "roles", "display", "family")),
        ("body family", ("typography", "roles", "body", "family")),
        ("type scale ratio", ("typography", "scale", "ratio")),
        ("columns", ("layout", "columns")),
        ("density", ("layout", "density")),
    ]
    for label, path in checks:
        a, b = _top(old, *path), _top(new, *path)
        if a != b:
            out.append(f"{label}: {a} -> {b}")
    oa, na = old.get("corpus", {}).get("sources"), new["corpus"]["sources"]
    if oa != na:
        out.insert(0, f"sources: {oa} -> {na}")
    return out


def render_markdown(p: dict) -> str:
    c, t, l, q = p["color"], p["typography"], p["layout"], p["qualitative"]
    lines = [f"# Design profile — {p['name']}", "",
             f"Learned {p['generated_at']} from **{p['corpus']['sources']} sources** "
             f"({', '.join(f'{v} {k}' for k, v in p['corpus']['roles'].items())}); "
             f"{p['corpus']['observed']} visually reviewed.", "",
             "| Area | Confidence |", "|---|---|"]
    lines += [f"| {k} | {v:.0%} |" for k, v in p["confidence"].items()]
    lines += ["", "## Color", "", "| Role | Color | Name | Share | Support |", "|---|---|---|---|---|"]
    for label, lst in (("paper", c["paper"][:2]), ("ink", c["ink"][:2]), ("accent", c["accents"][:6]),
                       ("mid neutral", c["mid_neutrals"][:2])):
        for x in lst:
            lines.append(f"| {label} | `{x['hex']}` | {x['name']} | {x['share']:.1%} | {x['support']:.0%} |")
    if c["declared"]:
        lines += ["", "Declared in text (briefs, guidelines, themes):", ""]
        lines += [f"- `{d['hex']}` {d['name']} — hint: {d['role_hint'] or '—'} (×{d['count']})" for d in c["declared"][:8]]
    lines += ["", f"Accent coverage across the corpus: {c['accent_coverage']:.1%}", "", "## Typography", ""]
    for r in ("display", "body", "mono"):
        x = t["roles"].get(r)
        if x:
            lines.append(f"- **{r}**: {x['family']} ({x['category']}, weight {x['weight']})"
                         + (f" → web/Figma substitute: {x['substitute']}" if x.get("substitute") else ""))
    s = t["scale"]
    lines += [f"- scale: {s['ratio']} ({s['ratio_name']}), raw fit {s['ratio_raw']}, levels {s['levels'][:6]}",
              f"- leading: body {t['leading']['body']}, display {t['leading']['display']}",
              f"- measure: {t['measure_chars']} chars/line; uppercase headings: {t['case']['headings_uppercase']}"]
    if t["declared"]:
        lines.append("- named in text: " + ", ".join(d["family"] for d in t["declared"][:6]))
    lines += ["", "## Layout", "",
              f"- margins (fraction of page width): {l['margins']}",
              f"- columns: {l['columns']} {l['columns_distribution']}, gutter ratio {l['gutter_ratio']}",
              f"- whitespace {l['whitespace']} → {l['density']}; image coverage {l['image_coverage']} → {l['imagery']}",
              "", "## Qualitative", ""]
    if q["observed_sources"]:
        lines.append("- mood: " + ", ".join(m["word"] for m in q["mood"][:8]))
        lines.append("- voice: " + ", ".join(v["word"] for v in q["voice"][:6]))
        lines.append("- decided: " + ", ".join(f"{k}={v}" for k, v in q["decided"].items()))
        lines += ["", "Principles:"] + [f"- {x['text']} ({len(x['sources'])} src)" for x in q["principles"][:10]]
        if q["locks"]:
            lines += ["", f"Locks from briefs: {q['locks']}"]
        if q["lock_conflicts"]:
            lines += [f"Lock conflicts: {q['lock_conflicts']}"]
    else:
        lines.append("_No visual reviews yet — run the design-analyst agent on each source._")
    return "\n".join(lines) + "\n"
