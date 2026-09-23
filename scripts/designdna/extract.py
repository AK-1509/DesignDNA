"""Per-source extraction: turn a PDF, image, deck, document, web file or text brief
into ``analysis.json`` plus page renders the design-analyst agent can look at."""
from __future__ import annotations

import hashlib
import html as html_lib
import math
import re
import statistics
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

from . import color as C
from . import fonts as F

try:
    import pymupdf  # PyMuPDF >= 1.24
except ImportError:  # pragma: no cover
    try:
        import fitz as pymupdf  # type: ignore
    except ImportError:
        pymupdf = None

PDF_EXT = {".pdf"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
TEXT_EXT = {".txt", ".md", ".markdown", ".rtf"}
OFFICE_EXT = {".docx", ".pptx"}
WEB_EXT = {".html", ".htm", ".css"}
SUPPORTED = PDF_EXT | IMG_EXT | TEXT_EXT | OFFICE_EXT | WEB_EXT

ROLES = ("brief", "magazine", "portfolio", "report", "reference")
_ROLE_KEYS = (
    ("brief", ("brief", "rfp", "rfq", "requirements", "scope", "sow", "guidelines", "brandbook", "brand")),
    ("portfolio", ("portfolio", "folio", "casestudy", "case", "showreel", "work")),
    ("report", ("report", "annual", "whitepaper", "study", "review", "findings", "esg", "sustainability")),
    ("magazine", ("magazine", "mag", "issue", "zine", "editorial", "journal", "quarterly", "edition", "vol")),
)

RENDER_EDGE = 1100   # px, long edge of review renders
PALETTE_EDGE = 160   # px, long edge of palette thumbnails


def guess_role(path: Path) -> str:
    tokens = [t for t in re.split(r"[^a-z0-9]+", path.stem.lower()) if t]
    for role, keys in _ROLE_KEYS:
        for t in tokens:
            for k in keys:
                if t == k or (len(k) > 4 and t.startswith(k)):
                    return role
    if path.suffix.lower() in TEXT_EXT | {".docx"}:
        return "brief"
    return "reference"


def file_id(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def _sample_indices(n: int, k: int) -> list[int]:
    if n <= 0:
        return []
    if n <= k:
        return list(range(n))
    if k <= 1:
        return [0]
    return sorted({round(i * (n - 1) / (k - 1)) for i in range(k)})


def _flatten(im: Image.Image) -> Image.Image:
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        return bg.convert("RGB")
    return im.convert("RGB")


def _pixels(im: Image.Image, edge: int = PALETTE_EDGE) -> np.ndarray:
    small = im.copy()
    small.thumbnail((edge, edge))
    return np.asarray(small, dtype=float).reshape(-1, 3) / 255.0


def _hist(counter: Counter, top: int = 12) -> list[dict]:
    total = sum(counter.values()) or 1
    return [{"hex": k, "weight": round(v / total, 4)} for k, v in counter.most_common(top) if v / total >= 0.003]


# ---------------------------------------------------------------------------
# Declared values found in text (briefs and brand guidelines state them outright)
# ---------------------------------------------------------------------------

HEX_RE = re.compile(r"(?<![\w&/])#([0-9A-Fa-f]{6})\b")
RGB_FN_RE = re.compile(r"\brgba?\s*\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})", re.I)
RGB_WORDS_RE = re.compile(r"\bR\s*[:=]?\s*(\d{1,3})\s*[,/ ]\s*G\s*[:=]?\s*(\d{1,3})\s*[,/ ]\s*B\s*[:=]?\s*(\d{1,3})\b")
CMYK_RE = re.compile(r"\bC\s*[:=]?\s*(\d{1,3})\s*[,/ ]\s*M\s*[:=]?\s*(\d{1,3})\s*[,/ ]\s*Y\s*[:=]?\s*(\d{1,3})"
                     r"\s*[,/ ]\s*K\s*[:=]?\s*(\d{1,3})\b")
PANTONE_RE = re.compile(r"\b(?:PANTONE|Pantone|PMS)\s+([0-9]{2,5}(?:\s?[A-Z]{1,3})?|[A-Z][a-z]+ [A-Z][a-z]+)")
ROLE_HINTS = [
    ("primary", r"primary|brand|main|core|hero|signature|key colou?r"),
    ("secondary", r"secondary|supporting|complementary"),
    ("accent", r"accent|highlight|pop|call.to.action|cta"),
    ("background", r"background|\bbg\b|paper|canvas|surface"),
    ("text", r"\btext\b|body copy|ink|type colou?r|foreground"),
    ("neutral", r"neutral|gr[ae]y|stone|charcoal|slate"),
    ("success", r"success|positive"), ("warning", r"warning|caution"), ("danger", r"danger|error|negative"),
]


def _context(text: str, start: int, end: int) -> str:
    s = text[max(0, start - 70):min(len(text), end + 30)]
    return re.sub(r"\s+", " ", s).strip()


def _hint(before: str, after: str = "") -> str | None:
    """Role named next to a color value. The same line before the value wins (nearest mention),
    then the wider context before it, then the text just after it on the same line."""
    def nearest(s: str, last: bool) -> str | None:
        best, pos = None, -1 if last else 10 ** 9
        for role, pat in ROLE_HINTS:
            for m in re.finditer(pat, s.lower()):
                if (last and m.start() > pos) or (not last and m.start() < pos):
                    best, pos = role, m.start()
        return best
    line_before = re.split(r"[\n;|•]|\s[-–]\s", before)[-1]
    line_after = re.split(r"[\n;|•]|\s[-–]\s", after)[0]
    return nearest(line_before, True) or nearest(line_after, False) or nearest(before, True)


def find_declared_colors(text: str, limit: int = 60) -> list[dict]:
    found: list[dict] = []

    def add(hex_value: str, kind: str, m: re.Match, approx: bool = False):
        ctx = _context(text, m.start(), m.end())
        found.append({"hex": hex_value.upper(), "kind": kind, "approx": approx,
                      "role_hint": _hint(text[max(0, m.start() - 70):m.start()], text[m.end():m.end() + 40]),
                      "context": ctx})

    for m in HEX_RE.finditer(text):
        add("#" + m.group(1), "hex", m)
    for rx, kind in ((RGB_FN_RE, "rgb"), (RGB_WORDS_RE, "rgb")):
        for m in rx.finditer(text):
            r, g, b = (int(x) for x in m.groups()[:3])
            if max(r, g, b) <= 255:
                add(C.rgb_to_hex((r / 255, g / 255, b / 255)), kind, m)
    for m in CMYK_RE.finditer(text):
        c, mm, y, k = (min(100, int(x)) / 100 for x in m.groups())
        add(C.rgb_to_hex(((1 - c) * (1 - k), (1 - mm) * (1 - k), (1 - y) * (1 - k))), "cmyk", m, approx=True)
    pantones = []
    for m in PANTONE_RE.finditer(text):
        pantones.append({"name": "Pantone " + m.group(1).strip(), "context": _context(text, m.start(), m.end())})
    # de-duplicate (same hex, keep first context)
    seen, out = set(), []
    for d in found:
        if d["hex"] in seen:
            continue
        seen.add(d["hex"])
        out.append(d)
    out = out[:limit]
    if pantones:
        out.append({"pantone": pantones[:20]})
    return out


def _split_declared(items: list[dict]) -> tuple[list[dict], list[dict]]:
    colors = [d for d in items if "hex" in d]
    pantone = next((d["pantone"] for d in items if "pantone" in d), [])
    return colors, pantone


def _text_block(text: str, out_dir: Path, cap: int = 300_000) -> dict:
    text = text[:cap]
    (out_dir / "text.txt").write_text(text, encoding="utf-8")
    declared, pantone = _split_declared(find_declared_colors(text))
    return {"chars": len(text), "file": "text.txt", "declared_colors": declared, "pantone": pantone,
            "font_mentions": F.find_mentions(text)}


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def extract_pdf(path: Path, out_dir: Path, max_pages: int = 40, renders: int = 10) -> dict:
    if pymupdf is None:
        raise RuntimeError("PyMuPDF is not installed: pip install pymupdf")
    doc = pymupdf.open(path)
    n = doc.page_count
    idx = _sample_indices(n, max_pages)
    render_idx = {idx[i] for i in _sample_indices(len(idx), renders)}
    (out_dir / "renders").mkdir(parents=True, exist_ok=True)
    text_flags = pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES

    font_stats: dict[str, dict] = {}
    size_chars: Counter = Counter()
    text_colors: Counter = Counter()
    vec_colors: Counter = Counter()
    leading_pairs: list[tuple[float, float]] = []
    lines: list[tuple[float, str, int]] = []
    margins, columns, gutters, img_cov, txt_cov, ws = [], [], [], [], [], []
    pixels, render_files = [], []
    page_sizes: Counter = Counter()

    for pi in idx:
        page = doc[pi]
        W, H = page.rect.width, page.rect.height
        area = max(W * H, 1.0)
        page_sizes[f"{round(W)}x{round(H)}"] += 1
        d = page.get_text("dict", flags=text_flags)
        boxes: list[tuple[tuple, int]] = []
        page_spans: list[tuple[tuple, float, int]] = []
        for b in d.get("blocks", []):
            if b.get("type", 0) != 0:
                continue
            bchars, prev = 0, None
            for line in b.get("lines", []):
                spans = [s for s in line.get("spans", []) if s.get("text", "").strip()]
                if not spans:
                    continue
                lsize: Counter = Counter()
                lchars = 0
                for s in spans:
                    nc = len(s["text"].strip())
                    size = round(float(s["size"]) * 2) / 2
                    st = font_stats.setdefault(s["font"], {"chars": 0, "sizes": Counter(), "flags": Counter()})
                    st["chars"] += nc
                    st["sizes"][size] += nc
                    st["flags"][int(s.get("flags", 0))] += nc
                    size_chars[size] += nc
                    text_colors[C.int_to_hex(int(s.get("color", 0)))] += nc
                    lsize[size] += nc
                    lchars += nc
                    page_spans.append((tuple(s["bbox"]), size, nc))
                bchars += lchars
                main = lsize.most_common(1)[0][0]
                baseline = float(spans[0].get("origin", (0, line["bbox"][3]))[1])
                if prev and abs(prev[0] - main) < 0.6 and main > 0:
                    r = (baseline - prev[1]) / main
                    if 0.8 <= r <= 3.0:
                        leading_pairs.append((main, r))
                prev = (main, baseline)
                lines.append((main, " ".join(s["text"].strip() for s in spans)[:160], lchars))
            if bchars >= 20:
                boxes.append((tuple(b["bbox"]), bchars))

        if boxes:
            x0 = min(bb[0] for bb, _ in boxes)
            y0 = min(bb[1] for bb, _ in boxes)
            x1 = max(bb[2] for bb, _ in boxes)
            y1 = max(bb[3] for bb, _ in boxes)
            margins.append({"left": max(0, x0) / W, "right": max(0, W - x1) / W,
                            "top": max(0, y0) / W, "bottom": max(0, H - y1) / W})
            txt_cov.append(min(1.0, sum((bb[2] - bb[0]) * (bb[3] - bb[1]) for bb, _ in boxes) / area))
            cols, gut = _columns(page_spans, W)
            columns.append(cols)
            gutters.extend(gut)

        try:
            cov = 0.0
            for info in page.get_image_info():
                r = pymupdf.Rect(info["bbox"]) & page.rect
                if not r.is_empty:
                    cov += r.width * r.height
            img_cov.append(min(1.0, cov / area))
        except Exception:
            pass

        try:
            for p in page.get_drawings()[:3000]:
                rect = p.get("rect")
                if rect is None:
                    continue
                r = pymupdf.Rect(rect) & page.rect
                a = 0.0 if r.is_empty else r.width * r.height / area
                if p.get("fill") is not None and a > 0:
                    vec_colors[C.rgb_to_hex(p["fill"])] += a
                if p.get("color") is not None and p.get("width"):
                    vec_colors[C.rgb_to_hex(p["color"])] += min(0.01, (r.width + r.height) * float(p["width"]) / area)
        except Exception:
            pass

        z = PALETTE_EDGE / max(W, H)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(z, z), alpha=False)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        px = np.asarray(im, dtype=float).reshape(-1, 3) / 255.0
        pixels.append(px)
        ws.append(C.whitespace_ratio(px))
        if pi in render_idx:
            z = RENDER_EDGE / max(W, H)
            pix = page.get_pixmap(matrix=pymupdf.Matrix(z, z), alpha=False)
            name = f"renders/p{pi + 1:03d}.png"
            pix.save(str(out_dir / name))
            render_files.append(name)

    text = "\n\n".join(doc[i].get_text() for i in range(min(n, 120)))
    meta = {k: v for k, v in (doc.metadata or {}).items() if k in ("title", "subject", "creator", "producer") and v}
    doc.close()

    typography = _typography(font_stats, size_chars, leading_pairs, lines)
    all_px = np.concatenate(pixels) if pixels else np.zeros((0, 3))
    layout = {
        "margins": {k: _median([m[k] for m in margins]) for k in ("top", "right", "bottom", "left")} if margins else None,
        "columns": max(Counter(columns).items(), key=lambda kv: (kv[1], kv[0]))[0] if columns else None,
        "gutter_ratio": _median(gutters),
        "image_coverage": _mean(img_cov),
        "text_coverage": _mean(txt_cov),
        "whitespace": _mean(ws),
        "page_size_pt": page_sizes.most_common(1)[0][0] if page_sizes else None,
        "orientation": _orientation(page_sizes),
    }
    return {
        "kind": "pdf", "meta": meta,
        "pages": {"count": n, "sampled": len(idx), "renders": render_files},
        "typography": typography,
        "color": {"page_palette": C.palette(all_px, k=10), "text_colors": _hist(text_colors),
                  "vector_colors": _hist(vec_colors)},
        "layout": layout,
        "text": _text_block(text, out_dir),
    }


def _columns(spans, W) -> tuple[int, list[float]]:
    """Count text columns from vertical whitespace 'rivers' in the x-occupancy of body-size spans.
    (Block bboxes are unreliable: MuPDF merges spans that share a baseline across a gutter.)"""
    if not spans:
        return 1, []
    sizes = Counter()
    for _, size, nc in spans:
        sizes[size] += nc
    body = sizes.most_common(1)[0][0]
    occ = np.zeros(int(W) + 2)
    lo, hi = W, 0.0
    for bb, size, nc in spans:
        if 0.8 * body <= size <= 1.25 * body and nc >= 2:
            a, b = max(0, int(bb[0])), min(int(W) + 1, int(math.ceil(bb[2])))
            if b > a:
                occ[a:b] += 1
                lo, hi = min(lo, a), max(hi, b)
    if occ.max() < 5 or hi <= lo:
        return 1, []
    empty = occ[int(lo):int(hi)] < 0.05 * occ.max()
    gutters, run = [], 0
    for e in list(empty) + [False]:
        if e:
            run += 1
        else:
            if 6 <= run <= 0.15 * W:
                gutters.append(run / W)
            run = 0
    return max(1, min(6, len(gutters) + 1)), gutters


def _typography(font_stats, size_chars, leading_pairs, lines) -> dict:
    if not size_chars:
        return {"fonts": [], "body_size": None}
    body = max(size_chars.items(), key=lambda kv: kv[1])[0]
    total = sum(size_chars.values())
    merged: dict[tuple, dict] = {}
    for raw, st in font_stats.items():
        flags = st["flags"].most_common(1)[0][0] if st["flags"] else 0
        p = F.parse_font_name(raw, flags)
        key = (p["family"], p["weight"], p["italic"])
        m = merged.setdefault(key, {**p, "chars": 0, "sizes": Counter()})
        m["chars"] += st["chars"]
        m["sizes"].update(st["sizes"])
    fonts = sorted(merged.values(), key=lambda f: -f["chars"])[:20]
    for f in fonts:
        f["share"] = round(f["chars"] / total, 4)
        f["sizes"] = {str(k): v for k, v in sorted(f["sizes"].items())}
    body_lead = [r for s, r in leading_pairs if abs(s - body) <= 0.6]
    disp_lead = [r for s, r in leading_pairs if s >= 1.5 * body]
    heads = [ln for ln in lines if ln[0] >= 1.4 * body and re.search(r"[A-Za-z]", ln[1])]
    labels = [ln for ln in lines if ln[0] <= 0.85 * body and re.search(r"[A-Za-z]{3}", ln[1])]
    body_lines = [ln[2] for ln in lines if abs(ln[0] - body) <= 0.6 and ln[2] >= 15]
    seen, headings = set(), []
    for s, t, _ in sorted(heads, key=lambda x: -x[0]):
        key = t.lower()
        if key not in seen:
            seen.add(key)
            headings.append({"size": s, "text": t})
        if len(headings) >= 25:
            break
    significant = [s for s, c in size_chars.items() if c >= 15]
    return {
        "fonts": fonts,
        "body_size": body,
        "sizes": {str(k): v for k, v in sorted(size_chars.items())},
        "max_display_ratio": round(max(significant) / body, 3) if significant and body else None,
        "leading_body": _median(body_lead),
        "leading_display": _median(disp_lead),
        "headings": headings,
        "headings_uppercase": _upper_ratio([t for _, t, _ in heads]),
        "labels_uppercase": _upper_ratio([t for _, t, _ in labels]),
        "measure_chars": float(np.percentile(body_lines, 75)) if len(body_lines) >= 10 else None,
    }


def _upper_ratio(texts: list[str]) -> float | None:
    texts = [t for t in texts if len(re.findall(r"[A-Za-z]", t)) >= 3]
    if not texts:
        return None
    return round(sum(1 for t in texts if t.upper() == t) / len(texts), 3)


def _median(xs):
    xs = [x for x in xs if x is not None]
    return round(float(statistics.median(xs)), 4) if xs else None


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(float(np.mean(xs)), 4) if xs else None


def _orientation(page_sizes: Counter) -> str | None:
    if not page_sizes:
        return None
    w, h = (int(x) for x in page_sizes.most_common(1)[0][0].split("x"))
    return "landscape" if w > h * 1.05 else "portrait" if h > w * 1.05 else "square"


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------

def extract_image(path: Path, out_dir: Path) -> dict:
    (out_dir / "renders").mkdir(parents=True, exist_ok=True)
    im = Image.open(path)
    try:
        im.seek(0)
    except Exception:
        pass
    im = _flatten(im)
    W, H = im.size
    review = im.copy()
    review.thumbnail((RENDER_EDGE, RENDER_EDGE))
    review.save(out_dir / "renders" / "image.png")
    px = _pixels(im, 220)
    return {
        "kind": "image", "meta": {"width": W, "height": H},
        "pages": {"count": 1, "sampled": 1, "renders": ["renders/image.png"]},
        "typography": {"fonts": [], "body_size": None},
        "color": {"page_palette": C.palette(px, k=8), "text_colors": [], "vector_colors": []},
        "layout": {"whitespace": round(C.whitespace_ratio(px), 4), "image_coverage": None,
                   "orientation": "landscape" if W > H * 1.05 else "portrait" if H > W * 1.05 else "square"},
        "text": None,
    }


# ---------------------------------------------------------------------------
# Office (docx / pptx): theme colors & fonts are declared intent
# ---------------------------------------------------------------------------

_THEME_SLOTS = ("dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6",
                "hlink", "folHlink")
_OFFICE_DEFAULT_ACCENTS = {"4472C4", "156082", "4F81BD", "5B9BD5", "0F9ED5"}
_OFFICE_DEFAULT_FONTS = {"Calibri", "Calibri Light", "Aptos", "Aptos Display", "Cambria", "Arial"}


def _parse_theme(xml: str) -> dict:
    colors = {}
    for slot in _THEME_SLOTS:
        m = re.search(rf"<a:{slot}>(.*?)</a:{slot}>", xml, re.S)
        if not m:
            continue
        inner = m.group(1)
        v = re.search(r'lastClr="([0-9A-Fa-f]{6})"', inner) or re.search(r'val="([0-9A-Fa-f]{6})"', inner)
        if v:
            colors[slot] = "#" + v.group(1).upper()
    fonts = {}
    for kind in ("majorFont", "minorFont"):
        m = re.search(rf"<a:{kind}>\s*<a:latin typeface=\"([^\"]*)\"", xml)
        if m and m.group(1):
            fonts["display" if kind == "majorFont" else "body"] = m.group(1)
    name = re.search(r'<a:clrScheme name="([^"]*)"', xml)
    default = (colors.get("accent1", "").lstrip("#") in _OFFICE_DEFAULT_ACCENTS
               or set(fonts.values()) <= _OFFICE_DEFAULT_FONTS and bool(fonts))
    return {"scheme": name.group(1) if name else None, "colors": colors, "fonts": fonts, "is_office_default": default}


def extract_office(path: Path, out_dir: Path) -> dict:
    (out_dir / "renders").mkdir(parents=True, exist_ok=True)
    ext = path.suffix.lower()
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        theme_file = next((n for n in sorted(names) if re.match(r"(word|ppt)/theme/theme\d+\.xml$", n)), None)
        theme = _parse_theme(z.read(theme_file).decode("utf-8", "ignore")) if theme_file else None
        if ext == ".docx":
            parts = [n for n in names if re.match(r"word/(document|header\d*|footer\d*)\.xml$", n)]
        else:
            parts = sorted((n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                           key=lambda s: int(re.search(r"(\d+)\.xml$", s).group(1)))
        xml_all = [z.read(p).decode("utf-8", "ignore") for p in parts]
        media = sorted((n for n in names if re.search(r"/media/.*\.(png|jpe?g|gif|bmp)$", n, re.I)),
                       key=lambda n: -z.getinfo(n).file_size)[:12]
        media_imgs = []
        for n in media:
            try:
                from io import BytesIO
                media_imgs.append(_flatten(Image.open(BytesIO(z.read(n)))))
            except Exception:
                continue

    texts, font_uses, sizes, colors = [], Counter(), Counter(), Counter()
    for xml in xml_all:
        if ext == ".docx":
            paras = re.split(r"</w:p>", xml)
            texts.extend("".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)) for p in paras)
            font_uses.update(re.findall(r'w:rFonts [^>]*w:ascii="([^"]+)"', xml))
            sizes.update(int(v) / 2 for v in re.findall(r'<w:sz w:val="(\d+)"', xml))
            colors.update("#" + v.upper() for v in re.findall(r'<w:color w:val="([0-9A-Fa-f]{6})"', xml))
            colors.update("#" + v.upper() for v in re.findall(r'w:fill="([0-9A-Fa-f]{6})"', xml))
        else:
            texts.append(" ".join(re.findall(r"<a:t>([^<]*)</a:t>", xml)))
            font_uses.update(f for f in re.findall(r'<a:latin typeface="([^"]+)"', xml) if not f.startswith("+"))
            sizes.update(int(v) / 100 for v in re.findall(r'<a:rPr[^>]*\bsz="(\d+)"', xml))
            colors.update("#" + v.upper() for v in re.findall(r'<a:srgbClr val="([0-9A-Fa-f]{6})"', xml))
    text = html_lib.unescape("\n".join(t for t in texts if t.strip()))

    fonts = []
    if theme:
        for role, fam in theme["fonts"].items():
            c = F.classify(fam)
            fonts.append({**c, "raw": fam, "weight": 700 if role == "display" else 400, "italic": False,
                          "chars": 1, "sizes": {}, "theme_role": role})
    tot = sum(font_uses.values()) or 1
    for fam, cnt in font_uses.most_common(8):
        c = F.classify(fam)
        fonts.append({**c, "raw": fam, "weight": 400, "italic": False, "chars": cnt, "share": round(cnt / tot, 3),
                      "sizes": {}})
    body = sizes.most_common(1)[0][0] if sizes else None
    significant = [s for s, c in sizes.items() if c >= 2]
    typography = {"fonts": fonts, "body_size": body,
                  "sizes": {str(k): v for k, v in sorted(sizes.items())},
                  "max_display_ratio": round(max(significant) / body, 3) if significant and body else None,
                  "note": "Office file: sizes are counted per run, not per character."}

    renders, media_px = [], []
    for i, im in enumerate(media_imgs):
        media_px.append(_pixels(im))
        if i < 6:
            r = im.copy()
            r.thumbnail((RENDER_EDGE, RENDER_EDGE))
            name = f"renders/media{i + 1:02d}.png"
            r.save(out_dir / name)
            renders.append(name)
    px = np.concatenate(media_px) if media_px else np.zeros((0, 3))
    return {
        "kind": ext.lstrip("."), "meta": {"parts": len(parts)},
        "theme": theme,
        "pages": {"count": len(parts), "sampled": len(parts), "renders": renders},
        "typography": typography,
        "color": {"page_palette": C.palette(px, k=8) if len(px) else [], "text_colors": [],
                  "vector_colors": _hist(colors)},
        "layout": {},
        "text": _text_block(text, out_dir),
    }


# ---------------------------------------------------------------------------
# Web (html / css) and plain text
# ---------------------------------------------------------------------------

def extract_web(path: Path, out_dir: Path) -> dict:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", raw, re.S | re.I)) if path.suffix != ".css" else raw
    css += "\n" + "\n".join(re.findall(r'style="([^"]*)"', raw))
    colors = Counter("#" + (h * 2 if len(h) == 3 else h).upper()
                     for h in re.findall(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", css))
    for r, g, b in re.findall(r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})", css):
        colors[C.rgb_to_hex((int(r) / 255, int(g) / 255, int(b) / 255))] += 1
    variables = [{"name": n, "hex": ("#" + v.upper()) if len(v) == 6 else "#" + "".join(c * 2 for c in v).upper()}
                 for n, v in re.findall(r"(--[\w-]+)\s*:\s*#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", css)]
    families = Counter()
    for decl in re.findall(r"font-family\s*:\s*([^;}{]+)", css):
        first = decl.split(",")[0].strip().strip("'\"")
        if first and not first.startswith("var("):
            families[first] += 1
    px_sizes = Counter(float(v) for v in re.findall(r"font-size\s*:\s*([\d.]+)px", css))
    px_sizes.update(float(v) * 16 for v in re.findall(r"font-size\s*:\s*([\d.]+)rem", css))
    body = text = None
    if path.suffix != ".css":
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
        text = html_lib.unescape(re.sub(r"<[^>]+>", " ", text))
        text = re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n\n", text)).strip()
    tot = sum(families.values()) or 1
    fonts = [{**F.classify(f), "raw": f, "weight": 400, "italic": False, "chars": c, "share": round(c / tot, 3),
              "sizes": {}} for f, c in families.most_common(6)]
    if px_sizes:
        body = min((s for s, _ in px_sizes.most_common(3)), key=lambda s: abs(s - 16))
    tb = _text_block(text or "", out_dir)
    tb["css_variables"] = variables[:80]
    return {
        "kind": "web", "meta": {},
        "pages": {"count": 1, "sampled": 1, "renders": []},
        "typography": {"fonts": fonts, "body_size": body, "sizes": {str(k): v for k, v in sorted(px_sizes.items())},
                       "max_display_ratio": round(max(px_sizes) / body, 3) if px_sizes and body else None},
        "color": {"page_palette": [], "text_colors": [], "vector_colors": _hist(colors, 16)},
        "layout": {},
        "text": tb,
    }


def extract_text(path: Path, out_dir: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".rtf":
        text = re.sub(r"\\[a-z]+-?\d* ?|[{}]", "", text)
    return {
        "kind": "text", "meta": {},
        "pages": {"count": 1, "sampled": 1, "renders": []},
        "typography": {"fonts": [], "body_size": None},
        "color": {"page_palette": [], "text_colors": [], "vector_colors": []},
        "layout": {},
        "text": _text_block(text, out_dir),
    }


def extract(path: Path, out_dir: Path, max_pages: int = 40, renders: int = 10) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = path.suffix.lower()
    if ext in PDF_EXT:
        return extract_pdf(path, out_dir, max_pages=max_pages, renders=renders)
    if ext in IMG_EXT:
        return extract_image(path, out_dir)
    if ext in OFFICE_EXT:
        return extract_office(path, out_dir)
    if ext in WEB_EXT:
        return extract_web(path, out_dir)
    if ext in TEXT_EXT:
        return extract_text(path, out_dir)
    raise ValueError(f"Unsupported file type: {path.suffix}")
