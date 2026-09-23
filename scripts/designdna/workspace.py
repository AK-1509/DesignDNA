"""The on-disk corpus: ``.design-dna/`` in the user's project.

.design-dna/
  config.json                  name, created, settings
  corpus/<id>/source.json      what was ingested (path, role, weight, tags)
  corpus/<id>/analysis.json    machine extraction (extract.py)
  corpus/<id>/renders/*.png    page renders for visual review
  corpus/<id>/text.txt         extracted text
  observations/<id>.json       qualitative review written by the design-analyst agent
  overrides.json               explicit decisions (win over everything learned)
  profile.json / profile.md    the learned design profile (learn.py)
  history/                     previous profiles, so drift is visible
  output/<slug>/               generated design system (generate.py)
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve(path: str | None = None) -> Path:
    if path:
        return Path(path).expanduser().resolve()
    env = os.environ.get("DESIGN_DNA_HOME")
    if env:
        return Path(env).expanduser().resolve()
    return (Path.cwd() / ".design-dna").resolve()


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class Workspace:
    def __init__(self, root: Path):
        self.root = root

    # paths ---------------------------------------------------------------
    @property
    def corpus(self) -> Path:
        return self.root / "corpus"

    @property
    def observations(self) -> Path:
        return self.root / "observations"

    @property
    def output(self) -> Path:
        return self.root / "output"

    @property
    def profile_path(self) -> Path:
        return self.root / "profile.json"

    @property
    def overrides_path(self) -> Path:
        return self.root / "overrides.json"

    # lifecycle -----------------------------------------------------------
    def exists(self) -> bool:
        return (self.root / "config.json").exists()

    def init(self, name: str | None = None) -> dict:
        for p in (self.corpus, self.observations, self.output, self.root / "history"):
            p.mkdir(parents=True, exist_ok=True)
        cfg = read_json(self.root / "config.json", {}) or {}
        cfg.setdefault("created", now())
        if name:
            cfg["name"] = name
        cfg.setdefault("name", "Design DNA")
        cfg["version"] = 1
        write_json(self.root / "config.json", cfg)
        if not self.overrides_path.exists():
            write_json(self.overrides_path, {
                "_help": "Explicit decisions. Anything set here beats what was learned. Delete keys to let the corpus decide.",
                "name": None,
                "color": {"primary": None, "accent": None, "neutral": None, "background": None, "text": None},
                "typography": {"display": None, "body": None, "mono": None, "ratio": None, "base_px": None},
                "shape": {"corners": None, "elevation": None, "borders": None},
                "density": None,
            })
        gi = self.root / ".gitignore"
        if not gi.exists():
            gi.write_text("corpus/*/renders/\n", encoding="utf-8")
        return cfg

    @property
    def config(self) -> dict:
        return read_json(self.root / "config.json", {}) or {}

    # sources -------------------------------------------------------------
    def source_ids(self) -> list[str]:
        if not self.corpus.exists():
            return []
        return sorted(p.name for p in self.corpus.iterdir() if (p / "analysis.json").exists())

    def load_source(self, sid: str) -> dict:
        d = self.corpus / sid
        src = read_json(d / "source.json", {}) or {}
        src["analysis"] = read_json(d / "analysis.json", {}) or {}
        src["observation"] = read_json(self.observations / f"{sid}.json")
        return src

    def sources(self) -> list[dict]:
        return [self.load_source(s) for s in self.source_ids()]

    def overrides(self) -> dict:
        ov = read_json(self.overrides_path, {}) or {}
        return _prune(ov)


def _prune(d):
    """Drop None values and help keys so overrides only contain real decisions."""
    if isinstance(d, dict):
        out = {}
        for k, v in d.items():
            if k.startswith("_"):
                continue
            v = _prune(v)
            if v not in (None, {}, [], ""):
                out[k] = v
        return out
    return d
