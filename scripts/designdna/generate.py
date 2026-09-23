"""Write every output for a resolved design system."""
from __future__ import annotations

import shutil
from pathlib import Path

from . import export_docs, export_figma, export_tokens
from .system import build_system
from .workspace import Workspace, read_json, write_json


def generate(ws: Workspace, name: str | None = None, out: Path | None = None, fmt: str = "legacy") -> tuple[dict, Path]:
    profile = read_json(ws.profile_path)
    if not profile:
        raise SystemExit("No profile yet. Run: dna.py learn")
    system = build_system(profile, ws.overrides(), name)
    out = out or (ws.output / system["slug"])
    out.mkdir(parents=True, exist_ok=True)
    d = export_tokens.DTCG(fmt)

    tokens = out / "tokens"
    write_json(tokens / "primitives.tokens.json", export_tokens.primitives(system, d))
    write_json(tokens / "color.light.tokens.json", export_tokens.semantic(system, "light"))
    write_json(tokens / "color.dark.tokens.json", export_tokens.semantic(system, "dark"))
    write_json(tokens / "typography.tokens.json", export_tokens.typography(system, d))
    write_json(tokens / "tokens.json", export_tokens.combined(system, d))
    (out / "tokens.css").write_text(export_tokens.css(system), encoding="utf-8")

    figma = out / "figma"
    sp = export_figma.spec(system)
    write_json(figma / "variables.json", sp)
    for fname, code in export_figma.scripts(sp).items():
        (figma / fname).write_text(code, encoding="utf-8")

    md = export_docs.design_md(system)
    (out / "DESIGN.md").write_text(md, encoding="utf-8")
    (out / "preview.html").write_text(export_docs.preview_html(system), encoding="utf-8")

    # Claude Design bundle (a claude.ai/design design-system project): README guide, tokens,
    # full specimen, and one @dsCard preview per group for the Design System pane.
    cd = out / "claude-design"
    if cd.exists():
        shutil.rmtree(cd)
    (cd / "preview").mkdir(parents=True)
    (cd / "README.md").write_text(md, encoding="utf-8")
    shutil.copy(out / "tokens.css", cd / "tokens.css")
    shutil.copy(tokens / "tokens.json", cd / "tokens.json")
    shutil.copy(out / "preview.html", cd / "index.html")
    for fname, doc in export_docs.cards(system).items():
        (cd / "preview" / fname).write_text(doc, encoding="utf-8")

    write_json(out / "system.json", system)
    return system, out
