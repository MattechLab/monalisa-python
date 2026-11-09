"""Recreate the conditions of a MATLAB call before replaying it.

A few functions depend on the moment or on the file system rather than on their arguments. Their
recordings are replayed after restoring that state:

- ``bmTimeInSecond``: the date and time are rebuilt from the recorded value and the clock is frozen
  at that moment;
- ``bmCheckDir`` / ``bmCreateDir``: the recorded directories are recreated, as they were at the time
  of the call, inside the test's temporary directory.

``prepare`` returns a check to run after the replay (or None).
"""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np


def prepare(rec, tmp_path: Path, monkeypatch):
    setup = _SETUPS.get(rec.func)
    return setup(rec, tmp_path, monkeypatch) if setup else None


def _frozen_clock(rec, tmp_path, monkeypatch):
    # MATLAB: t = Second + Minute*60 + Hour*60^2 + Day*24*60^2 (Second with its fraction)
    t = float(np.asarray(rec.outputs[0]).item())
    day, rest = divmod(t, 24 * 60**2)
    hour, rest = divmod(rest, 60**2)
    minute, sec = divmod(rest, 60)
    now = dt.datetime(2026, 1, int(day), int(hour), int(minute), int(sec), round((sec % 1) * 1e6))

    class Clock:
        @staticmethod
        def now(tz=None):
            return now

    import monalisa.time.bmTimeInSecond as mod

    monkeypatch.setattr(mod, "dt", SimpleNamespace(datetime=Clock))
    return None


def _in_tmp(rec, tmp_path):
    """Move the recorded (absolute) directory into ``tmp_path``; returns the new path."""
    recorded = os.path.normpath(str(np.asarray(rec.inputs[0]).item()))
    moved = tmp_path / "fs" / recorded.lstrip(os.sep)
    rec.inputs[0] = np.array([str(moved)])
    return moved


def _check_dir(rec, tmp_path, monkeypatch):
    d = _in_tmp(rec, tmp_path)
    if np.asarray(rec.outputs[0]).item():  # the directory existed at the time of the call
        d.mkdir(parents=True)
    return None


def _create_dir(rec, tmp_path, monkeypatch):
    # bmMitosius_create only creates missing directories: none of them existed before the call
    d = _in_tmp(rec, tmp_path)

    def check():
        assert d.is_dir(), f"{rec.id}: the directory was not created"

    return check


_SETUPS = {"bmTimeInSecond": _frozen_clock, "bmCheckDir": _check_dir, "bmCreateDir": _create_dir}
