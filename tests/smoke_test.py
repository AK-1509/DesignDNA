"""End-to-end smoke test: fixtures -> ingest -> observations -> learn -> generate -> checks.

Run: python tests/smoke_test.py   (needs pymupdf, pillow, numpy; node optional for JS syntax checks)
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import make_fixtures  # noqa: E402
from designdna import color as C  # noqa: E402
from designdna.cli import main as dna  # noqa: E402


def run(*args):
    print("$ dna.py", " ".join(args))
    dna(list(args))


def check(cond, msg):
    print(("  ok  " if cond else "  FAIL ") + msg)
    if not cond:
        raise SystemExit(1)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="design-dna-"))
    fx, ws = tmp / "fixtures", tmp / "ws"
    make_fixtures.main(fx)
    run("-w", str(ws), "init", "--name", "Meridian")
    run("-w", str(ws), "ingest", str(fx))

    # unit checks on color math
    check(abs(C.contrast("#000000", "#FFFFFF") - 21) < 0.01, "contrast black/white = 21")
    check(C.oklab_to_hex(C.hex_to_oklab("#E4572E")) == "#E4572E", "OKLab round trip")
    ramp, anchor = C.ramp("#E4572E")
    check(ramp[anchor] == "#E4572E", f"ramp keeps anchor at {anchor}")

    sources = {s.name: s for s in (ws / "corpus").iterdir()}
    analyses = {json.loads((d / "source.json").read_text())["name"]: json.loads((d / "analysis.json").read_text())
                for d in sources.values()}
    mag = analyses["meridian-magazine-spring.pdf"]
    check(mag["typography"]["body_size"] == 9.5, f"magazine body size 9.5 (got {mag['typography']['body_size']})")
    check(mag["layout"]["columns"] == 2, f"magazine 2 columns (got {mag['layout']['columns']})")
    check(any(f["category"] == "serif" for f in mag["typography"]["fonts"]), "magazine has a serif face")
    check(len(mag["pages"]["renders"]) > 0, "magazine renders written")
    brief = analyses["meridian-brief.md"]
    hints = {d["hex"]: d["role_hint"] for d in brief["text"]["declared_colors"]}
    check(hints.get("#E4572E") == "primary", f"brief declares #E4572E as primary (got {hints.get('#E4572E')})")
    check(hints.get("#1D3557") == "secondary", f"brief declares #1D3557 as secondary (got {hints.get('#1D3557')})")
    check(hints.get("#F6F1E7") == "background", f"brief declares #F6F1E7 as background (got {hints.get('#F6F1E7')})")
    check("Playfair Display" in brief["text"]["font_mentions"], "brief mentions Playfair Display")
    deck = analyses["pitch-deck.pptx"]
    check(deck["theme"]["colors"]["accent1"] == "#E4572E" and not deck["theme"]["is_office_default"], "deck theme parsed")

    # simulate the design-analyst agent writing observations
    mag_id = next(k for k, d in sources.items() if json.loads((d / "source.json").read_text())["name"].startswith("meridian-magazine"))
    brief_id = next(k for k, d in sources.items() if json.loads((d / "source.json").read_text())["name"] == "meridian-brief.md")
    obs = ws / "observations"
    (obs / f"{mag_id}.json").write_text(json.dumps({
        "source_id": mag_id, "summary": "A restrained editorial magazine on warm paper.",
        "mood": ["editorial", "restrained", "warm"], "principles": ["Wide margins frame every spread", "One accent color per spread"],
        "composition": {"alignment": "left", "whitespace": "airy", "grid": "two-column text grid"},
        "shape": {"corners": "sharp", "borders": "hairline", "elevation": "flat"},
        "components_seen": ["pull quote", "kicker", "caption"], "voice": {"attributes": ["precise", "wry"]},
        "dos": ["Run photographs full bleed"], "donts": ["No drop shadows"], "confidence": 0.8}), encoding="utf-8")
    (obs / f"{brief_id}.json").write_text(json.dumps({
        "source_id": brief_id, "summary": "Rebrand brief for an essay publisher.", "mood": ["confident", "warm"],
        "principles": ["Make long reading comfortable on screen"],
        "brief": {"project": "Meridian Press rebrand", "audience": "curious readers 25-55",
                  "goals": ["Feel editorial and confident"],
                  "locks": {"colors": {"primary": "#E4572E", "background": "#F6F1E7"},
                            "fonts": {"display": "Playfair Display", "body": "Source Serif 4"}}},
        "voice": {"attributes": ["warm", "precise", "wry"]}}), encoding="utf-8")
    try:
        run("-w", str(ws), "validate")
    except SystemExit as e:
        check(e.code == 0, "observations validate")

    run("-w", str(ws), "learn")
    prof = json.loads((ws / "profile.json").read_text(encoding="utf-8"))
    top = prof["color"]["accents"][0]["hex"]
    check(C.delta_e(top, "#E4572E") < 0.06, f"top learned accent ≈ vermilion (got {top})")
    check(prof["typography"]["roles"]["body"]["category"] == "serif", "learned body face is serif")
    check(prof["qualitative"]["locks"]["colors"]["primary"] == "#E4572E", "brief lock captured")

    run("-w", str(ws), "generate")
    out = ws / "output" / "meridian"
    for f in ("DESIGN.md", "preview.html", "tokens.css", "tokens/tokens.json", "tokens/color.dark.tokens.json",
              "figma/variables.json", "figma/01-variables.js", "figma/02-styles.js", "figma/03-foundations.js",
              "claude-design/README.md"):
        check((out / f).exists(), f"wrote {f}")
    cards = sorted((out / "claude-design" / "preview").glob("*.html"))
    check(len(cards) >= 5 and all(c.read_text(encoding="utf-8").startswith("<!-- @dsCard group=") for c in cards),
          f"{len(cards)} Claude Design preview cards with @dsCard markers")
    system = json.loads((out / "system.json").read_text(encoding="utf-8"))
    check(system["color"]["primary"] == "#E4572E", "primary = brief lock")
    check(system["color"]["accent"] == "#1D3557", f"accent = declared secondary navy (got {system['color']['accent']})")
    check(system["color"]["base"]["paper"] == "#F6F1E7", "paper = brief lock")
    check(system["typography"]["families"]["display"]["name"] == "Playfair Display", "display font = brief lock")
    check(system["shape"]["corners"] == "sharp", "corners from visual review")
    check(all(r["pass"] for r in system["color"]["contrast"] if r["fg"].startswith("text.default")), "body text contrast passes")
    failing = [r for r in system["color"]["contrast"] if not r["pass"]]
    print(f"  info {len(failing)} contrast pairs below target: {[(r['mode'], r['fg'], r['ratio']) for r in failing]}")

    node = shutil.which("node")
    if node:
        for js in sorted((out / "figma").glob("*.js")):
            wrapped = tmp / (js.stem + ".check.mjs")
            wrapped.write_text("async function run(figma){\n" + js.read_text(encoding="utf-8") + "\n}\n", encoding="utf-8")
            r = subprocess.run([node, "--check", str(wrapped)], capture_output=True, text=True)
            check(r.returncode == 0, f"{js.name} parses as JS {r.stderr.strip()[:300]}")
    print(f"\nALL GOOD. Outputs in {out}")
    return out


if __name__ == "__main__":
    main()
