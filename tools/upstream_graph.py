"""Static inventory and call graph of the upstream MATLAB code.

Usage:
    python tools/upstream_graph.py /path/to/monalisa [--entry name,...] [--json out.json]

Without --entry, the entries are the demo pipelines that define the porting scope
(tutorial 1 and the static/chain/sheet reconstruction scripts). Prints the
functions of src/ reachable from the entries, leaves first (porting order).
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DEFAULT_ENTRIES = [
    "coilSensitivityEstimation_script",
    "binnings_script",
    "mitosius_script",
    "reconstructions_script",
    "static_recon_calls_script",
    "chain_recon_calls_script",
    "sheet_recon_calls_script",
]

_STRING = re.compile(r"'[^'\n]*'")
_IDENT = re.compile(r"\b[A-Za-z_]\w*\b")


def _code(text: str) -> str:
    lines = []
    for line in text.splitlines():
        lines.append(_STRING.sub("''", line).split("%")[0])
    return "\n".join(lines)


def load_graph(root: Path) -> tuple[dict[str, Path], dict[str, list[str]]]:
    """Return (name -> file, name -> called names) for src/, demo/ and third_part/."""
    files: dict[str, Path] = {}
    for sub in ("src", "demo", "third_part"):
        for p in sorted((root / sub).rglob("*.m")):
            files.setdefault(p.stem, p)
    names = set(files)
    deps = {}
    for name, p in files.items():
        tokens = set(_IDENT.findall(_code(p.read_text(errors="replace"))))
        deps[name] = sorted((tokens & names) - {name})
    return files, deps


def closure(entries, deps) -> list[str]:
    """Functions reachable from ``entries``, in dependency order (leaves first)."""
    seen: set[str] = set()
    stack = list(entries)
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        stack.extend(deps.get(n, []))
    order: list[str] = []
    visited: set[str] = set()

    def visit(n):
        if n in visited:
            return
        visited.add(n)
        for d in deps.get(n, []):
            if d in seen:
                visit(d)
        order.append(n)

    for n in sorted(seen):
        visit(n)
    return order


def scope(root: Path, entries=None) -> list[dict]:
    files, deps = load_graph(root)
    order = closure(entries or DEFAULT_ENTRIES, deps)
    out = []
    for n in order:
        p = files[n]
        rel = p.relative_to(root)
        if rel.parts[0] != "src":
            continue
        code_lines = [l for l in _code(p.read_text(errors="replace")).splitlines() if l.strip()]
        out.append(
            {
                "name": n,
                "path": str(rel),
                "code_lines": len(code_lines),
                "deps": [d for d in deps[n] if d in order],
            }
        )
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", type=Path)
    ap.add_argument("--entry", default=None, help="comma separated entry functions/scripts")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()
    entries = args.entry.split(",") if args.entry else None
    items = scope(args.root, entries)
    for it in items:
        print(f"{it['code_lines']:5d}  {it['path']}")
    print(f"{len(items)} functions, {sum(i['code_lines'] for i in items)} code lines")
    if args.json:
        args.json.write_text(json.dumps(items, indent=1))


if __name__ == "__main__":
    main()
