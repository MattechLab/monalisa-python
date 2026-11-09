"""Replay every MATLAB golden recording against the ported function."""

from pathlib import Path

import pytest
from environment import prepare
from tolerances import KNOWN_DIVERGENCES, tolerance_for

import monalisa
from monalisa.testing import compare, from_matlab, iter_records, load_record, replay

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "matlab"
RECORDS = list(iter_records(FIXTURES))


def _id(path: Path) -> str:
    return f"{path.parts[-3]}/{path.parts[-2]}/{path.stem}"


@pytest.mark.parity
@pytest.mark.skipif(not RECORDS, reason=f"no MATLAB recordings in {FIXTURES}")
@pytest.mark.parametrize("path", RECORDS, ids=_id)
def test_parity(path, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # some functions (witness of iterative solvers) write files
    rec = load_record(path)
    func = monalisa.find_function(rec.func)
    if func is None:
        pytest.skip(f"{rec.func} not ported yet")
    reason = KNOWN_DIVERGENCES.get(rec.id) or KNOWN_DIVERGENCES.get(rec.func)
    if reason:
        pytest.xfail(reason)

    check = prepare(rec, tmp_path, monkeypatch)
    outs = replay(rec, func)
    if check:
        check()
    tol = tolerance_for(rec.func)
    issues = []
    for i, (py, ml) in enumerate(zip(outs, rec.outputs, strict=True)):
        issues += compare(py, from_matlab(ml, "output"), tol, f"out{i + 1}")
    assert not issues, f"{rec.id} (caller {rec.caller}):\n  " + "\n  ".join(issues)
