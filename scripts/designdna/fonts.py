"""Font name parsing, classification and open-font substitutes.

PDFs embed names like ``ABCDEF+HelveticaNeueLTStd-BdCn``. We normalise those to a
family, weight and style, classify the family, and suggest a Google Fonts
substitute (Google Fonts are available in both browsers and Figma).
"""
from __future__ import annotations

import re

# name -> (category, open substitute or None when the family itself is on Google Fonts)
KNOWN: dict[str, tuple[str, str | None]] = {
    # serif
    "Adobe Garamond": ("serif", "EB Garamond"), "Garamond": ("serif", "EB Garamond"),
    "EB Garamond": ("serif", None), "Sabon": ("serif", "EB Garamond"), "Janson": ("serif", "EB Garamond"),
    "Caslon": ("serif", "Libre Caslon Text"), "Libre Caslon Text": ("serif", None),
    "Baskerville": ("serif", "Libre Baskerville"), "Libre Baskerville": ("serif", None),
    "Times New Roman": ("serif", "Tinos"), "Times": ("serif", "Tinos"), "Tinos": ("serif", None),
    "Georgia": ("serif", "Gelasio"), "Minion": ("serif", "Crimson Pro"), "Crimson Pro": ("serif", None),
    "Crimson Text": ("serif", None), "Palatino": ("serif", "Crimson Pro"), "Plantin": ("serif", "Crimson Pro"),
    "Didot": ("serif", "Playfair Display"), "Bodoni": ("serif", "Bodoni Moda"), "Bodoni Moda": ("serif", None),
    "Playfair Display": ("serif", None), "Playfair": ("serif", None),
    "Tiempos Headline": ("serif", "Newsreader"), "Tiempos": ("serif", "Source Serif 4"),
    "GT Sectra": ("serif", "Fraunces"), "Canela": ("serif", "Cormorant Garamond"),
    "Freight": ("serif", "Libre Caslon Text"), "Chronicle": ("serif", "Source Serif 4"),
    "Miller": ("serif", "Source Serif 4"), "Publico": ("serif", "Newsreader"), "Lyon": ("serif", "Newsreader"),
    "Mercury": ("serif", "Source Serif 4"), "Utopia": ("serif", "Source Serif 4"), "Charter": ("serif", "Source Serif 4"),
    "Cambria": ("serif", "Caladea"), "Merriweather": ("serif", None), "Lora": ("serif", None),
    "Source Serif 4": ("serif", None), "Source Serif Pro": ("serif", "Source Serif 4"), "Source Serif": ("serif", "Source Serif 4"),
    "Cormorant Garamond": ("serif", None), "Cormorant": ("serif", None), "Fraunces": ("serif", None),
    "Newsreader": ("serif", None), "PT Serif": ("serif", None), "Noto Serif": ("serif", None),
    "Spectral": ("serif", None), "DM Serif Display": ("serif", None), "Instrument Serif": ("serif", None),
    "Gelasio": ("serif", None), "Caladea": ("serif", None),
    # sans
    "Neue Haas Grotesk": ("sans", "Inter"), "Neue Haas Unica": ("sans", "Inter"),
    "Helvetica Neue": ("sans", "Inter"), "Neue Helvetica": ("sans", "Inter"), "Helvetica": ("sans", "Inter"),
    "Arial": ("sans", "Arimo"), "Arimo": ("sans", None), "Akzidenz Grotesk": ("sans", "Inter Tight"),
    "Univers": ("sans", "Inter"), "Frutiger": ("sans", "Open Sans"), "Myriad": ("sans", "PT Sans"),
    "Futura": ("sans", "Jost"), "Avenir Next": ("sans", "Nunito Sans"), "Avenir": ("sans", "Nunito Sans"),
    "Gill Sans": ("sans", "Cabin"), "Proxima Nova": ("sans", "Montserrat"), "Gotham": ("sans", "Montserrat"),
    "Circular": ("sans", "DM Sans"), "Graphik": ("sans", "Inter"), "GT America Mono": ("mono", "IBM Plex Mono"),
    "GT America": ("sans", "Inter Tight"), "GT Walsheim": ("sans", "DM Sans"), "Apercu": ("sans", "DM Sans"),
    "Neue Montreal": ("sans", "Inter"), "Sohne": ("sans", "Inter"), "Söhne": ("sans", "Inter"),
    "Aktiv Grotesk": ("sans", "Inter"), "Brandon Grotesque": ("sans", "Josefin Sans"), "Gilroy": ("sans", "Manrope"),
    "Calibri": ("sans", "Carlito"), "Carlito": ("sans", None), "Aptos": ("sans", "Inter"),
    "Segoe UI": ("sans", "Noto Sans"), "Verdana": ("sans", "Noto Sans"), "Tahoma": ("sans", "Noto Sans"),
    "Franklin Gothic": ("sans", "Libre Franklin"), "News Gothic": ("sans", "Libre Franklin"),
    "Trade Gothic": ("sans", "Archivo"), "DIN": ("sans", "Barlow"), "Eurostile": ("sans", "Michroma"),
    "SF Pro": ("sans", "Inter"), "San Francisco": ("sans", "Inter"), "Roboto": ("sans", None),
    "Inter Tight": ("sans", None), "Inter": ("sans", None), "Open Sans": ("sans", None), "Lato": ("sans", None),
    "Montserrat": ("sans", None), "Poppins": ("sans", None), "Source Sans 3": ("sans", None),
    "Source Sans Pro": ("sans", "Source Sans 3"), "IBM Plex Sans": ("sans", None), "Work Sans": ("sans", None),
    "DM Sans": ("sans", None), "Manrope": ("sans", None), "Nunito Sans": ("sans", None), "Noto Sans": ("sans", None),
    "Raleway": ("sans", None), "Archivo": ("sans", None), "Space Grotesk": ("sans", None), "Syne": ("sans", None),
    "Outfit": ("sans", None), "Plus Jakarta Sans": ("sans", None), "Figtree": ("sans", None), "Geist Mono": ("mono", None),
    "Geist": ("sans", None), "Public Sans": ("sans", None), "Barlow": ("sans", None), "Karla": ("sans", None),
    "Rubik": ("sans", None), "Mulish": ("sans", None), "PT Sans": ("sans", None), "Libre Franklin": ("sans", None),
    "Jost": ("sans", None), "Josefin Sans": ("sans", None), "Cabin": ("sans", None), "Instrument Sans": ("sans", None),
    "Hanken Grotesk": ("sans", None), "Schibsted Grotesk": ("sans", None), "Bricolage Grotesque": ("sans", None),
    "Chivo": ("sans", None), "Michroma": ("sans", None),
    # display
    "Knockout": ("display", "Oswald"), "Druk": ("display", "Anton"), "Impact": ("display", "Anton"),
    "Anton": ("display", None), "Bebas Neue": ("display", None), "Oswald": ("display", None),
    "Abril Fatface": ("display", None),
    # mono
    "Courier New": ("mono", "Courier Prime"), "Courier": ("mono", "Courier Prime"), "Courier Prime": ("mono", None),
    "Consolas": ("mono", "Inconsolata"), "Menlo": ("mono", "JetBrains Mono"), "Monaco": ("mono", "JetBrains Mono"),
    "SF Mono": ("mono", "JetBrains Mono"), "JetBrains Mono": ("mono", None), "IBM Plex Mono": ("mono", None),
    "Fira Code": ("mono", None), "Fira Mono": ("mono", None), "Source Code Pro": ("mono", None),
    "Space Mono": ("mono", None), "Roboto Mono": ("mono", None), "Inconsolata": ("mono", None),
    "DM Mono": ("mono", None),
    # slab
    "Rockwell": ("slab", "Roboto Slab"), "Clarendon": ("slab", "Zilla Slab"), "Museo Slab": ("slab", "Zilla Slab"),
    "Roboto Slab": ("slab", None), "Zilla Slab": ("slab", None), "Arvo": ("slab", None),
}

DEFAULT_SUBSTITUTE = {"serif": "Source Serif 4", "sans": "Inter", "mono": "JetBrains Mono",
                      "display": "Inter Tight", "slab": "Roboto Slab"}
GENERIC_STACK = {
    "serif": 'Georgia, "Times New Roman", serif',
    "slab": 'Rockwell, Georgia, serif',
    "sans": 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
    "display": 'system-ui, -apple-system, "Segoe UI", sans-serif',
    "mono": 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
}

_COMPACT = {re.sub(r"[^a-z0-9]", "", k.lower()): k for k in KNOWN}
_COMPACT_KEYS = sorted(_COMPACT, key=len, reverse=True)

WEIGHT_WORDS = [
    (r"hairline|thin", 100), (r"extra ?light|ultra ?light|xlight", 200), (r"light|lt\b", 300),
    (r"semi ?bold|demi ?bold|demi|sb\b|smbd", 600), (r"extra ?bold|ultra ?bold|xbold|heavy|hv\b", 800),
    (r"black|blk|ultra\b|fat", 900), (r"bold|bd\b", 700), (r"medium|med\b|md\b", 500),
    (r"regular|roman|book|normal|text|rg\b|reg\b", 400),
]
_SUFFIX_JUNK = re.compile(r"(LTStd|LTPro|Std|Pro|PSMT|MT|PS|LT|OT|Web|Variable|VF)$")


def _split_camel(s: str) -> str:
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def weight_from_style(style: str) -> int:
    s = style.lower()
    for pat, w in WEIGHT_WORDS:
        if re.search(pat, s):
            return w
    return 400


def lookup(family: str) -> tuple[str, str, str | None] | None:
    """Return (canonical name, category, substitute) for a known family, by compact prefix match."""
    compact = re.sub(r"[^a-z0-9]", "", family.lower())
    for key in _COMPACT_KEYS:
        if compact.startswith(key):
            name = _COMPACT[key]
            cat, sub = KNOWN[name]
            return name, cat, sub
    return None


def parse_font_name(raw: str, flags: int = 0) -> dict:
    """Parse an embedded font name. PyMuPDF span flags: 2 italic, 4 serif, 8 mono, 16 bold."""
    name = re.sub(r"^[A-Z]{6}\+", "", raw or "").strip() or "Unknown"
    if "," in name:
        fam_part, style_part = name.split(",", 1)
    elif "-" in name:
        fam_part, style_part = name.split("-", 1)
    else:
        fam_part, style_part = name, ""
    fam_part = _SUFFIX_JUNK.sub("", fam_part)
    style_all = style_part + " " + (fam_part if not style_part else "")
    weight = weight_from_style(style_part or fam_part)
    if flags & 16 and weight < 600:
        weight = 700
    italic = bool(flags & 2) or bool(re.search(r"italic|oblique|\bit\b|ita\b", style_all.lower()))
    known = lookup(fam_part)
    if known:
        family, category, substitute = known
    else:
        family = _split_camel(fam_part).replace("_", " ")
        category = "mono" if flags & 8 else "serif" if flags & 4 else "sans"
        substitute = DEFAULT_SUBSTITUTE[category]
    return {"raw": name, "family": family, "weight": weight, "italic": italic,
            "category": category, "substitute": substitute, "known": bool(known)}


def classify(family: str, fallback: str = "sans") -> dict:
    known = lookup(family)
    if known:
        name, cat, sub = known
        return {"family": name, "category": cat, "substitute": sub, "known": True}
    low = family.lower()
    cat = fallback
    if re.search(r"mono|code|courier|typewriter", low):
        cat = "mono"
    elif re.search(r"serif|garamond|caslon|roman|antiqua|didone|times", low) and "sans" not in low:
        cat = "serif"
    return {"family": family, "category": cat, "substitute": DEFAULT_SUBSTITUTE[cat], "known": False}


def web_family(family: str, category: str, substitute: str | None) -> str:
    """The family to actually load from Google Fonts / use in Figma."""
    return substitute or family


def css_stack(family: str, category: str, substitute: str | None) -> str:
    parts = [f'"{family}"']
    if substitute and substitute != family:
        parts.append(f'"{substitute}"')
    parts.append(GENERIC_STACK.get(category, GENERIC_STACK["sans"]))
    return ", ".join(parts)


# Family names that are also ordinary words, places or people: only count them near type vocabulary.
AMBIGUOUS = {
    "Times", "DIN", "Lyon", "Miller", "Courier", "Georgia", "Circular", "Freight", "Charter", "Mercury",
    "Chronicle", "Utopia", "Druk", "Knockout", "Impact", "Minion", "Oswald", "Anton", "Barlow", "Karla",
    "Rubik", "Syne", "Outfit", "Geist", "Jost", "Cabin", "Chivo", "Lato", "Lora", "Arvo", "Inter", "Monaco",
    "Cambria", "Tahoma", "Canela", "Publico", "Sabon", "Janson", "Plantin", "Gotham", "Avenir", "Univers",
    "Tinos", "Arimo", "Gelasio", "Caladea", "Carlito", "Aptos", "Calibri", "Menlo", "Consolas", "Merriweather",
    "Spectral", "Fraunces", "Newsreader", "Figtree", "Raleway", "Poppins", "Manrope", "Mulish", "Archivo",
}
_TYPE_WORDS = (r"font|fonts|typeface|typefaces|type|family|typography|headline|headlines|heading|headings|"
               r"body|copy|text|set\s+in|display|serif|sans|mono")
_STYLE_WORDS = r"font|typeface|family|pro|std|bold|regular|light|medium|italic|display|text|sans|serif|mono"


def find_mentions(text: str) -> dict[str, int]:
    """Known typeface names mentioned in free text (briefs often name the brand fonts)."""
    counts: dict[str, int] = {}
    for name in sorted(KNOWN, key=len, reverse=True):
        esc = re.escape(name)
        if name in AMBIGUOUS:
            before = rf"\b(?:{_TYPE_WORDS})\b[\s:,\-–—(\"']+(?:[\w\-]+[\s,]+){{0,3}}{esc}\b(?!-)"
            after = rf"\b{esc}\b(?!-)[\s,]+(?:[\w\-]+[\s,]+){{0,2}}(?:{_STYLE_WORDS})\b"
            n = len(re.findall(before, text, flags=re.I)) + len(re.findall(after, text))
            n = min(n, len(re.findall(rf"\b{esc}\b", text)))
        else:
            n = len(re.findall(rf"\b{esc}\b(?!-)", text, flags=re.I))
        if n and not any(name in longer for longer in counts):
            counts[name] = n
    return counts
