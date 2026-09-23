"""Color science: sRGB <-> OKLab/OKLCH, WCAG contrast, k-means palettes and tonal ramps."""
from __future__ import annotations

import math

import numpy as np

# ---------------------------------------------------------------------------
# Conversions
# ---------------------------------------------------------------------------

_M1 = np.array([
    [0.4122214708, 0.5363325363, 0.0514459929],
    [0.2119034982, 0.6806995451, 0.1073969566],
    [0.0883024619, 0.2817188376, 0.6299787005],
])
_M2 = np.array([
    [0.2104542553, 0.7936177850, -0.0040720468],
    [1.9779984951, -2.4285922050, 0.4505937099],
    [0.0259040371, 0.7827717662, -0.8086757660],
])
_M2_INV = np.array([
    [1.0, 0.3963377774, 0.2158037573],
    [1.0, -0.1055613458, -0.0638541728],
    [1.0, -0.0894841775, -1.2914855480],
])
_M1_INV = np.array([
    [4.0767416621, -3.3077115913, 0.2309699292],
    [-1.2684380046, 2.6097574011, -0.3413193965],
    [-0.0041960863, -0.7034186147, 1.7076147010],
])


def hex_to_rgb(value: str) -> tuple[float, float, float]:
    h = value.strip().lstrip("#")
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h[:3])
    h = h[:6]
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def rgb_to_hex(rgb) -> str:
    return "#" + "".join(f"{round(max(0.0, min(1.0, float(c))) * 255):02X}" for c in rgb)


def int_to_hex(value: int) -> str:
    return f"#{value & 0xFFFFFF:06X}"


def to_linear(c):
    c = np.asarray(c, dtype=float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    c = np.asarray(c, dtype=float)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(np.maximum(c, 0), 1 / 2.4) - 0.055)


def srgb_to_oklab(rgb):
    """rgb: array (...,3) in 0..1 -> OKLab (...,3)."""
    lms = to_linear(rgb) @ _M1.T
    return np.cbrt(lms) @ _M2.T


def oklab_to_linear(lab):
    lms_ = np.asarray(lab, dtype=float) @ _M2_INV.T
    return (lms_ ** 3) @ _M1_INV.T


def oklab_to_srgb(lab):
    return to_srgb(oklab_to_linear(lab))


def hex_to_oklab(value: str) -> np.ndarray:
    return srgb_to_oklab(np.array(hex_to_rgb(value)))


def oklab_to_hex(lab) -> str:
    return rgb_to_hex(np.clip(oklab_to_srgb(lab), 0, 1))


def oklab_to_oklch(lab):
    L, a, b = (float(x) for x in lab)
    C = math.hypot(a, b)
    h = math.degrees(math.atan2(b, a)) % 360
    return L, C, h


def oklch_to_oklab(L: float, C: float, h: float) -> np.ndarray:
    r = math.radians(h)
    return np.array([L, C * math.cos(r), C * math.sin(r)])


def hex_to_oklch(value: str) -> tuple[float, float, float]:
    return oklab_to_oklch(hex_to_oklab(value))


def in_gamut(lab, eps: float = 1e-4) -> bool:
    lin = oklab_to_linear(lab)
    return bool(np.all(lin >= -eps) and np.all(lin <= 1 + eps))


def oklch_to_hex(L: float, C: float, h: float) -> str:
    """Convert OKLCH to hex, reducing chroma (binary search) until the color fits sRGB."""
    L = max(0.0, min(1.0, L))
    if in_gamut(oklch_to_oklab(L, C, h)):
        return oklab_to_hex(oklch_to_oklab(L, C, h))
    lo, hi = 0.0, C
    for _ in range(24):
        mid = (lo + hi) / 2
        if in_gamut(oklch_to_oklab(L, mid, h)):
            lo = mid
        else:
            hi = mid
    return oklab_to_hex(oklch_to_oklab(L, lo, h))


# ---------------------------------------------------------------------------
# Contrast
# ---------------------------------------------------------------------------

def luminance(value: str) -> float:
    r, g, b = to_linear(np.array(hex_to_rgb(value)))
    return float(0.2126 * r + 0.7152 * g + 0.0722 * b)


def contrast(fg: str, bg: str) -> float:
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def delta_e(a: str, b: str) -> float:
    return float(np.linalg.norm(hex_to_oklab(a) - hex_to_oklab(b)))


# ---------------------------------------------------------------------------
# Palette extraction
# ---------------------------------------------------------------------------

def kmeans(X: np.ndarray, k: int, iters: int = 30, seed: int = 7):
    """Plain k-means with k-means++ seeding. Returns (centers, counts)."""
    rng = np.random.default_rng(seed)
    n = len(X)
    k = max(1, min(k, n))
    centers = [X[rng.integers(n)]]
    d2 = np.sum((X - centers[0]) ** 2, axis=1)
    for _ in range(1, k):
        total = d2.sum()
        if total <= 1e-12:
            break
        i = rng.choice(n, p=d2 / total)
        centers.append(X[i])
        d2 = np.minimum(d2, np.sum((X - X[i]) ** 2, axis=1))
    C = np.array(centers)
    labels = np.zeros(n, dtype=int)
    for _ in range(iters):
        dist = ((X[:, None, :] - C[None, :, :]) ** 2).sum(-1)
        labels = dist.argmin(1)
        new = np.array([X[labels == j].mean(0) if np.any(labels == j) else C[j] for j in range(len(C))])
        if np.allclose(new, C, atol=1e-5):
            C = new
            break
        C = new
    return C, np.bincount(labels, minlength=len(C))


def palette(pixels: np.ndarray, k: int = 10, merge: float = 0.035, min_share: float = 0.004,
            max_samples: int = 40000, seed: int = 7) -> list[dict]:
    """pixels: (N,3) sRGB 0..1. Returns [{hex, weight}] sorted by weight (weights sum to 1)."""
    if pixels is None or len(pixels) == 0:
        return []
    px = np.asarray(pixels, dtype=float).reshape(-1, 3)
    if len(px) > max_samples:
        idx = np.random.default_rng(seed).choice(len(px), max_samples, replace=False)
        px = px[idx]
    lab = srgb_to_oklab(px)
    centers, counts = kmeans(lab, k, seed=seed)
    clusters = [[c, float(n)] for c, n in zip(centers, counts) if n > 0]
    clusters.sort(key=lambda x: -x[1])
    merged: list[list] = []
    for c, n in clusters:
        for m in merged:
            if np.linalg.norm(m[0] - c) < merge:
                m[0] = (m[0] * m[1] + c * n) / (m[1] + n)
                m[1] += n
                break
        else:
            merged.append([c, n])
    total = sum(n for _, n in merged)
    out = [{"hex": oklab_to_hex(c), "weight": round(n / total, 4)} for c, n in merged if n / total >= min_share]
    out.sort(key=lambda d: -d["weight"])
    return out


def whitespace_ratio(pixels: np.ndarray, tol: float = 0.03) -> float:
    """Share of pixels that match the dominant (background) color."""
    px = np.asarray(pixels, dtype=float).reshape(-1, 3)
    if len(px) == 0:
        return 0.0
    q = np.round(px * 15).astype(int)
    keys = q[:, 0] * 256 + q[:, 1] * 16 + q[:, 2]
    mode = np.bincount(keys).argmax()
    bg = np.array([mode // 256, (mode // 16) % 16, mode % 16]) / 15
    lab = srgb_to_oklab(px)
    d = np.linalg.norm(lab - srgb_to_oklab(bg), axis=1)
    return float(np.mean(d < tol))


# ---------------------------------------------------------------------------
# Ramps
# ---------------------------------------------------------------------------

STEPS = (50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950)
RAMP_L = {50: 0.975, 100: 0.945, 200: 0.89, 300: 0.81, 400: 0.72, 500: 0.63,
          600: 0.54, 700: 0.46, 800: 0.38, 900: 0.30, 950: 0.22}
NEUTRAL_L = {50: 0.985, 100: 0.962, 200: 0.918, 300: 0.86, 400: 0.72, 500: 0.58,
             600: 0.48, 700: 0.40, 800: 0.30, 900: 0.225, 950: 0.165}


def nearest_step(L: float, table: dict = RAMP_L) -> int:
    return min(table, key=lambda s: abs(table[s] - L))


def ramp(base_hex: str, anchor: bool = True) -> tuple[dict[int, str], int]:
    """Tonal ramp 50..950 around a base color. The base color lands exactly on its
    nearest step (so brand colors survive untouched). Returns (ramp, anchor_step)."""
    L0, C0, h = hex_to_oklch(base_hex)
    step0 = nearest_step(L0)
    out: dict[int, str] = {}
    for s in STEPS:
        Lt = RAMP_L[s]
        if Lt >= L0:
            span = max(1.0 - L0, 1e-3)
        else:
            span = max(L0 - 0.12, 1e-3)
        t = min(1.0, abs(Lt - L0) / span)
        Ct = C0 * (1 - 0.75 * t ** 2)
        out[s] = oklch_to_hex(Lt, Ct, h)
    if anchor:
        out[step0] = base_hex.upper()
    return out, step0


def neutral_ramp(hue: float, chroma: float) -> dict[int, str]:
    chroma = max(0.0, min(chroma, 0.02))
    return {s: oklch_to_hex(NEUTRAL_L[s], chroma * (0.6 if s in (50, 950) else 1.0), hue) for s in STEPS}


def mix(a: str, b: str, t: float) -> str:
    """Mix in OKLab: t=0 -> a, t=1 -> b."""
    return oklab_to_hex(hex_to_oklab(a) * (1 - t) + hex_to_oklab(b) * t)


def hue_distance(h1: float, h2: float) -> float:
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)


def describe(value: str) -> str:
    """Rough human color name, for docs."""
    L, C, h = hex_to_oklch(value)
    if C < 0.03:
        if L > 0.93:
            return "paper white" if C < 0.012 else "warm off-white" if 40 < h < 120 else "tinted white"
        if L < 0.28:
            return "near-black ink"
        return "grey"
    names = [(20, "red"), (45, "orange-red"), (70, "orange"), (100, "yellow"), (130, "chartreuse"),
             (165, "green"), (200, "teal"), (235, "cyan-blue"), (265, "blue"), (300, "violet"),
             (335, "magenta"), (360, "pink-red")]
    base = next(n for lim, n in names if h < lim)
    tone = "pale " if L > 0.85 else "dark " if L < 0.4 else "deep " if C > 0.15 and L < 0.55 else ""
    return tone + base
