"""Command line for design-dna. Run ``python dna.py --help``."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import __version__
from .workspace import Workspace, now, read_json, resolve, write_json

OBS_REQUIRED = ("source_id", "summary", "mood", "principles")


def _ws(args) -> Workspace:
    ws = Workspace(resolve(args.workspace))
    if args.cmd not in ("init",) and not ws.exists():
        ws.init()
    return ws


def cmd_init(args):
    ws = Workspace(resolve(args.workspace))
    cfg = ws.init(args.name)
    print(f"Workspace ready: {ws.root}  (name: {cfg['name']})")


def _expand(paths: list[str]) -> list[Path]:
    from .extract import SUPPORTED
    out = []
    for p in paths:
        path = Path(p).expanduser()
        if path.is_dir():
            out += sorted(f for f in path.rglob("*") if f.is_file() and f.suffix.lower() in SUPPORTED
                          and not any(part.startswith(".") for part in f.relative_to(path).parts))
        elif path.is_file():
            out.append(path)
        else:
            print(f"  ! not found: {p}")
    return out


def cmd_ingest(args):
    from .extract import ROLES, SUPPORTED, extract, file_id, guess_role
    ws = _ws(args)
    files = _expand(args.paths)
    if not files:
        sys.exit("Nothing to ingest.")
    results = []
    for f in files:
        if f.suffix.lower() not in SUPPORTED:
            print(f"  - skip (unsupported): {f.name}")
            continue
        sid = file_id(f)
        d = ws.corpus / sid
        role = args.role or guess_role(f)
        if role not in ROLES:
            sys.exit(f"Unknown role {role!r}. Use one of: {', '.join(ROLES)}")
        if (d / "analysis.json").exists() and not args.force:
            src = read_json(d / "source.json", {})
            changed = src.get("role") != role and args.role or (args.weight is not None and src.get("weight") != args.weight)
            if changed:
                src.update({"role": role if args.role else src.get("role"),
                            "weight": args.weight if args.weight is not None else src.get("weight", 1.0)})
                write_json(d / "source.json", src)
                print(f"  = {f.name} [{sid}] already ingested; updated role/weight")
            else:
                print(f"  = {f.name} [{sid}] already ingested (use --force to re-extract)")
            results.append({"id": sid, "name": f.name, "status": "exists"})
            continue
        if d.exists():
            shutil.rmtree(d)
        print(f"  + {f.name} [{sid}] as {role} ...", flush=True)
        try:
            analysis = extract(f, d, max_pages=args.pages, renders=args.renders)
        except Exception as e:  # keep going on bad files
            print(f"    ! failed: {e}")
            shutil.rmtree(d, ignore_errors=True)
            results.append({"id": sid, "name": f.name, "status": f"failed: {e}"})
            continue
        analysis["id"] = sid
        write_json(d / "analysis.json", analysis)
        write_json(d / "source.json", {"id": sid, "name": f.name, "path": str(f.resolve()), "role": role,
                                       "weight": args.weight if args.weight is not None else 1.0,
                                       "tags": args.tag or [], "ingested_at": now()})
        t = analysis.get("typography") or {}
        c = analysis.get("color") or {}
        print(f"    pages {analysis['pages']['count']}, renders {len(analysis['pages']['renders'])}, "
              f"fonts {len(t.get('fonts') or [])}, palette {len(c.get('page_palette') or [])}, "
              f"declared colors {len((analysis.get('text') or {}).get('declared_colors') or [])}")
        results.append({"id": sid, "name": f.name, "status": "ingested", "role": role})
    if args.json:
        print(json.dumps(results, indent=2))
    print(f"\nCorpus: {len(ws.source_ids())} sources. Next: review renders (design-analyst), then `dna.py learn`.")


def cmd_list(args):
    ws = _ws(args)
    rows = []
    for sid in ws.source_ids():
        s = ws.load_source(sid)
        a = s["analysis"]
        rows.append({"id": sid, "name": s.get("name"), "role": s.get("role"), "weight": s.get("weight"),
                     "kind": a.get("kind"), "pages": (a.get("pages") or {}).get("count"),
                     "renders": len((a.get("pages") or {}).get("renders") or []),
                     "observed": isinstance(s.get("observation"), dict)})
    if args.json:
        print(json.dumps(rows, indent=2))
        return
    if not rows:
        print("Corpus is empty.")
    for r in rows:
        print(f"{r['id']}  {r['role']:<9} {str(r['kind']):<5} w={r['weight']:<4} pages={str(r['pages']):<4} "
              f"{'reviewed' if r['observed'] else 'NOT REVIEWED':<12} {r['name']}")


def cmd_pending(args):
    """Sources that still need a visual review, with everything the analyst needs."""
    ws = _ws(args)
    out = []
    for sid in ws.source_ids():
        s = ws.load_source(sid)
        if isinstance(s.get("observation"), dict) and not args.all:
            continue
        d = ws.corpus / sid
        out.append({"id": sid, "name": s.get("name"), "role": s.get("role"),
                    "analysis": str(d / "analysis.json"),
                    "renders": [str(d / r) for r in (s["analysis"].get("pages") or {}).get("renders", [])],
                    "text": str(d / "text.txt") if (d / "text.txt").exists() else None,
                    "write_observation_to": str(ws.observations / f"{sid}.json")})
    print(json.dumps(out, indent=2))


def cmd_remove(args):
    ws = _ws(args)
    for sid in args.ids:
        d = ws.corpus / sid
        if d.exists():
            shutil.rmtree(d)
            obs = ws.observations / f"{sid}.json"
            if obs.exists():
                obs.unlink()
            print(f"removed {sid}")
        else:
            print(f"no such source: {sid}")


def cmd_set(args):
    ws = _ws(args)
    d = ws.corpus / args.id
    src = read_json(d / "source.json")
    if not src:
        sys.exit(f"no such source: {args.id}")
    if args.role:
        src["role"] = args.role
    if args.weight is not None:
        src["weight"] = args.weight
    write_json(d / "source.json", src)
    print(f"{args.id}: role={src['role']} weight={src['weight']}")


def cmd_validate(args):
    ws = _ws(args)
    paths = [Path(p) for p in args.files] if args.files else sorted(ws.observations.glob("*.json"))
    ok = True
    for p in paths:
        try:
            o = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"✗ {p.name}: invalid JSON ({e})")
            ok = False
            continue
        problems = [f"missing '{k}'" for k in OBS_REQUIRED if not o.get(k)]
        if o.get("source_id") and o["source_id"] not in ws.source_ids():
            problems.append(f"source_id {o['source_id']} not in corpus")
        for k in ("mood", "principles", "dos", "donts", "components_seen", "typography_notes", "color_notes"):
            if k in o and not isinstance(o[k], list):
                problems.append(f"'{k}' must be a list")
        shape = o.get("shape") or {}
        if shape.get("corners") and shape["corners"] not in ("sharp", "subtle", "soft", "round", "pill"):
            problems.append("shape.corners must be sharp|subtle|soft|round|pill")
        if shape.get("elevation") and shape["elevation"] not in ("flat", "subtle", "layered"):
            problems.append("shape.elevation must be flat|subtle|layered")
        ws_ = (o.get("composition") or {}).get("whitespace")
        if ws_ and ws_ not in ("airy", "balanced", "dense"):
            problems.append("composition.whitespace must be airy|balanced|dense")
        if problems:
            ok = False
            print(f"✗ {p.name}: " + "; ".join(problems))
        else:
            print(f"✓ {p.name}")
    sys.exit(0 if ok else 1)


def cmd_learn(args):
    from .learn import learn
    ws = _ws(args)
    profile, changes = learn(ws)
    c, t, l = profile["color"], profile["typography"], profile["layout"]
    print(f"Learned from {profile['corpus']['sources']} sources ({profile['corpus']['observed']} reviewed).")
    acc = ", ".join(f"{a['hex']} {a['name']}" for a in c["accents"][:4]) or "none"
    print(f"  accents: {acc}")
    print(f"  paper/ink: {(c['paper'] or [{'hex': '-'}])[0]['hex']} / {(c['ink'] or [{'hex': '-'}])[0]['hex']}")
    r = t["roles"]
    print(f"  display: {(r.get('display') or {}).get('family')}   body: {(r.get('body') or {}).get('family')}   "
          f"scale: {t['scale']['ratio']} ({t['scale']['ratio_name']})")
    print(f"  layout: {l['columns']} col, density {l['density']}, imagery {l['imagery']}")
    print("  confidence: " + ", ".join(f"{k} {v:.0%}" for k, v in profile["confidence"].items()))
    if changes:
        print("  changed since last run:\n    " + "\n    ".join(changes))
    if profile["qualitative"]["lock_conflicts"]:
        print(f"  ! brief lock conflicts: {profile['qualitative']['lock_conflicts']}")
    print(f"\nProfile: {ws.profile_path}  (summary: {ws.root / 'profile.md'})")


def cmd_generate(args):
    from .generate import generate
    ws = _ws(args)
    system, out = generate(ws, name=args.name, out=Path(args.out) if args.out else None, fmt=args.format)
    fails = [r for r in system["color"]["contrast"] if not r["pass"]]
    print(f"Generated '{system['name']}' → {out}")
    for f in ("DESIGN.md", "preview.html", "tokens.css", "tokens/tokens.json", "figma/01-variables.js",
              "figma/02-styles.js", "figma/03-foundations.js", "claude-design/README.md"):
        print(f"  {out / f}")
    print(f"  primary {system['color']['primary']}  accent {system['color']['accent']}  "
          f"display {system['typography']['families']['display']['name']}  body {system['typography']['families']['body']['name']}")
    if fails:
        print("  ! contrast below target: " + ", ".join(f"{r['mode']} {r['fg']}/{r['bg']} {r['ratio']}" for r in fails))


def cmd_status(args):
    ws = _ws(args)
    ids = ws.source_ids()
    observed = sum(1 for s in ids if (ws.observations / f"{s}.json").exists())
    prof = read_json(ws.profile_path)
    outs = sorted(p.name for p in ws.output.iterdir()) if ws.output.exists() else []
    print(f"workspace: {ws.root}\nsources: {len(ids)} ({observed} reviewed)\n"
          f"profile: {prof['generated_at'] if prof else 'not learned yet'}\n"
          f"overrides: {json.dumps(ws.overrides())}\noutputs: {', '.join(outs) or 'none'}")
    if prof:
        newest = max(((ws.corpus / s / 'source.json').stat().st_mtime for s in ids), default=0)
        obs_new = max((p.stat().st_mtime for p in ws.observations.glob('*.json')), default=0)
        if max(newest, obs_new) > ws.profile_path.stat().st_mtime:
            print("! corpus or observations changed since the profile was learned. Run `learn` again.")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(prog="dna.py", description="design-dna: learn a design system from design documents.")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--workspace", "-w", help="workspace dir (default: $DESIGN_DNA_HOME or ./.design-dna)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="create a workspace")
    s.add_argument("--name")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("ingest", help="extract files or folders into the corpus")
    s.add_argument("paths", nargs="+")
    s.add_argument("--role", choices=["brief", "magazine", "portfolio", "report", "reference"],
                   help="default: guessed from the filename")
    s.add_argument("--weight", type=float, help="relative influence (default 1.0)")
    s.add_argument("--tag", action="append")
    s.add_argument("--pages", type=int, default=40, help="max PDF pages analysed (evenly sampled)")
    s.add_argument("--renders", type=int, default=10, help="pages rendered for visual review")
    s.add_argument("--force", action="store_true")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_ingest)

    s = sub.add_parser("list", help="list sources")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_list)

    s = sub.add_parser("pending", help="JSON of sources awaiting visual review")
    s.add_argument("--all", action="store_true", help="include already reviewed sources")
    s.set_defaults(fn=cmd_pending)

    s = sub.add_parser("set", help="change a source's role or weight")
    s.add_argument("id")
    s.add_argument("--role", choices=["brief", "magazine", "portfolio", "report", "reference"])
    s.add_argument("--weight", type=float)
    s.set_defaults(fn=cmd_set)

    s = sub.add_parser("remove", help="remove sources from the corpus")
    s.add_argument("ids", nargs="+")
    s.set_defaults(fn=cmd_remove)

    s = sub.add_parser("validate", help="validate observation files")
    s.add_argument("files", nargs="*")
    s.set_defaults(fn=cmd_validate)

    s = sub.add_parser("learn", help="aggregate the corpus into profile.json")
    s.set_defaults(fn=cmd_learn)

    s = sub.add_parser("generate", help="build the design system outputs")
    s.add_argument("--name")
    s.add_argument("--out")
    s.add_argument("--format", choices=["legacy", "2025"], default="legacy",
                   help="DTCG value format: legacy strings (widest tool support) or 2025.10 objects")
    s.set_defaults(fn=cmd_generate)

    s = sub.add_parser("status", help="workspace summary")
    s.set_defaults(fn=cmd_status)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
