"""Generate PORTING_STATUS.md: scope, port state and MATLAB parity per function.

Usage:
    python tools/port_status.py /path/to/monalisa [--fixtures fixtures/matlab] [--out PORTING_STATUS.md]

For every function of the porting scope (tools/upstream_graph.py) it reports
whether it is ported, how many MATLAB recordings exist and the result of
replaying them (worst relative L2 error over all outputs and records).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import tempfile
import traceback
from collections import defaultdict
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parents[1] / "tests" / "parity"))

from environment import prepare  # noqa: E402
from tolerances import KNOWN_DIVERGENCES, tolerance_for  # noqa: E402
from upstream_graph import scope  # noqa: E402

import monalisa  # noqa: E402
from monalisa._mat import cell_items, iscell  # noqa: E402
from monalisa.testing import compare, from_matlab, iter_records, load_record, replay  # noqa: E402


def _rel_l2(py, ml) -> float:
    """Worst relative L2 error over the numeric leaves of an output."""
    if ml is None or py is None:
        return 0.0
    if hasattr(ml, "parity_fields"):
        return max([_rel_l2(py.parity_fields()[k], v) for k, v in ml.parity_fields().items()] or [0.0])
    if isinstance(ml, dict):
        return max([_rel_l2(py.get(k) if isinstance(py, dict) else getattr(py, k, None), v)
                    for k, v in ml.items() if k != "_class"] or [0.0])
    if isinstance(ml, np.ndarray) and ml.dtype == object:
        if not iscell(py):
            return np.inf
        return max([_rel_l2(p, m) for p, m in zip(cell_items(py), cell_items(ml), strict=False)] or [0.0])
    if isinstance(ml, str):
        return 0.0 if py == ml else np.inf
    a = np.asarray(py)
    b = np.asarray(ml)
    if a.size != b.size or a.dtype == object:
        return np.inf
    if b.size == 0:
        return 0.0
    a = a.reshape(b.shape, order="F").astype(np.complex128)
    b = b.astype(np.complex128)
    ok = np.isfinite(b) & np.isfinite(a)
    nb = np.linalg.norm(b[ok])
    d = np.linalg.norm(a[ok] - b[ok])
    return float(d / nb) if nb > 0 else float(d)


def run(fixtures: Path):
    results = defaultdict(lambda: {"n": 0, "pass": 0, "fail": 0, "xfail": 0, "error": 0, "rel_l2": 0.0,
                                   "issues": []})
    for path in iter_records(fixtures):
        func_name = path.parent.name
        r = results[func_name]
        r["n"] += 1
        func = monalisa.find_function(func_name)
        if func is None:
            continue
        rec = load_record(path)
        if KNOWN_DIVERGENCES.get(rec.id) or KNOWN_DIVERGENCES.get(rec.func):
            r["xfail"] += 1
            continue
        try:
            with tempfile.TemporaryDirectory() as tmp, pytest.MonkeyPatch.context() as mp:
                check = prepare(rec, Path(tmp), mp)
                outs = replay(rec, func)
                if check:
                    check()
            issues = []
            for i, (py, ml) in enumerate(zip(outs, rec.outputs, strict=True)):
                mlc = from_matlab(ml, "output")
                issues += compare(py, mlc, tolerance_for(func_name), f"out{i + 1}")
                r["rel_l2"] = max(r["rel_l2"], _rel_l2(py, mlc))
            if issues:
                r["fail"] += 1
                r["issues"].append(f"{rec.id}: {issues[0]}")
            else:
                r["pass"] += 1
        except Exception as exc:  # noqa: BLE001
            r["error"] += 1
            r["issues"].append(f"{rec.id}: {type(exc).__name__}: {exc}")
            traceback.print_exc()
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("upstream", type=Path)
    ap.add_argument("--fixtures", type=Path, default=Path(__file__).parents[1] / "fixtures" / "matlab")
    ap.add_argument("--out", type=Path, default=Path(__file__).parents[1] / "PORTING_STATUS.md")
    args = ap.parse_args()

    items = scope(args.upstream)
    results = run(args.fixtures)
    index = monalisa._function_index()

    rows = []
    n_ported = n_validated = 0
    lines_ported = 0
    for it in items:
        name = it["name"]
        ported = name in index
        r = results.get(name)
        if ported:
            n_ported += 1
            lines_ported += it["code_lines"]
        if r is None or r["n"] == 0:
            parity = "no recording" if ported else ""
        elif not ported:
            parity = f"{r['n']} recorded"
        elif r["fail"] or r["error"]:
            parity = f"**FAIL** {r['pass']}/{r['n']}"
        else:
            parity = f"{r['pass']}/{r['n']} ok" + (f" ({r['xfail']} known div.)" if r["xfail"] else "")
            if r["pass"]:
                n_validated += 1
        rel = f"{r['rel_l2']:.1e}" if (r and ported and r["pass"]) else ""
        mark = "yes" if ported else ""
        rows.append(f"| `{name}` | {it['path']} | {it['code_lines']} | {mark} | {parity} | {rel} |")

    total_lines = sum(i["code_lines"] for i in items)
    head = [
        "# Porting status",
        "",
        f"Generated {dt.date.today().isoformat()} by `tools/port_status.py` against upstream "
        f"commit `{monalisa.UPSTREAM_COMMIT[:7]}`.",
        "",
        f"- Scope: **{len(items)} functions** of `src/` reachable from the demo pipelines "
        f"({total_lines} code lines).",
        f"- Ported: **{n_ported}** ({lines_ported} code lines, {100 * lines_ported / total_lines:.0f} %).",
        f"- Validated against MATLAB recordings: **{n_validated}**.",
        "",
        "*rel L2* is the worst relative L2 error over all recorded calls and outputs.",
        "",
        "| Function | Upstream file | Code lines | Ported | MATLAB parity | worst rel L2 |",
        "|---|---|---:|:---:|---|---:|",
    ]
    args.out.write_text("\n".join(head + rows) + "\n")
    fails = {k: v["issues"] for k, v in results.items() if v["issues"]}
    if fails:
        print(json.dumps(fails, indent=1)[:4000])
    print(f"wrote {args.out}: {n_ported}/{len(items)} ported, {n_validated} validated")


if __name__ == "__main__":
    main()
