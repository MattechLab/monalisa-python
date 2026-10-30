"""End-to-end comparison of tutorial 1 (Python port vs MATLAB).

Opt-in (slow, needs the tutorial raw data and the MATLAB outputs of
tools/matlab_capture/scenarios/scenario_tutorial_recon.m):

    MONALISA_E2E_DATA=/path/to/data_8_tutorial_1 pytest tests/e2e -s

``MONALISA_E2E_PY=<dir>`` reuses an existing Python run instead of running the pipeline.
A report is written to ``<python output dir>/e2e_report.json``.
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest
import scipy.io as sio

from monalisa.readWrite._mat73 import loadmat73
from monalisa.testing.metrics import rel_l2, summary

ROOT = Path(__file__).resolve().parents[2]
ML_DIR = ROOT / "fixtures" / "matlab_e2e" / "tutorial_1"
DATA = os.environ.get("MONALISA_E2E_DATA")

pytestmark = pytest.mark.skipif(
    DATA is None or not (ML_DIR / "reconstructions.mat").exists(),
    reason="set MONALISA_E2E_DATA and run scenario_tutorial_recon first",
)

REPORT = {}


@pytest.fixture(scope="module")
def py_dir(tmp_path_factory):
    out = os.environ.get("MONALISA_E2E_PY")
    if out:
        return Path(out)
    out = tmp_path_factory.mktemp("tutorial_1")
    sys.path.insert(0, str(ROOT / "examples" / "tutorial_1"))
    import tutorial_1

    tutorial_1.main(["--data", DATA, "--out", str(out)])
    return out


@pytest.fixture(scope="module", autouse=True)
def write_report(py_dir):
    yield
    (py_dir / "e2e_report.json").write_text(json.dumps(REPORT, indent=1))
    print(json.dumps(REPORT, indent=1))


def test_binning_masks_identical(py_dir):
    ml = sio.loadmat(ML_DIR / "binning.mat", variable_names=["allLinesMask", "sequentialMask"])
    py = loadmat73(py_dir / "binning.mat")
    for k in ("allLinesMask", "sequentialMask"):
        np.testing.assert_array_equal(py[k], ml[k])
    REPORT["binning"] = "identical"


def test_coil_sensitivity(py_dir):
    C_ml = sio.loadmat(ML_DIR / "coil_sensitivity_map.mat")["C"]
    C_py = loadmat73(py_dir / "coil_sensitivity_map.mat")["C"]
    REPORT["coil_sensitivity_C"] = summary(C_py, C_ml)
    assert REPORT["coil_sensitivity_C"]["rel_l2"] < 1e-3


def test_mitosius_preparation(py_dir):
    ml = loadmat73(ML_DIR / "mitosius_prep.mat")
    py = loadmat73(py_dir / "mitosius_prep.mat")
    REPORT["volume_elements"] = {"rel_l2": rel_l2(py["ve_tot"], ml["ve_tot"])}
    REPORT["normalization_x_tot"] = summary(py["x_tot"], ml["x_tot"])
    nv = float(np.ravel(py["normalize_val"])[0]) / float(np.ravel(ml["normalize_val"])[0]) - 1
    REPORT["normalize_val_rel_diff"] = nv
    assert abs(nv) < 1e-3
    assert REPORT["normalization_x_tot"]["rel_l2"] < 1e-3


def test_gridded_reconstructions(py_dir):
    ml = loadmat73(ML_DIR / "reconstructions.mat")
    py = loadmat73(py_dir / "reconstructions.mat")
    REPORT["x0_allLines"] = summary(py["x0"], ml["x0"])
    x1 = ml["x1"]
    for i in range(x1.size):
        REPORT[f"x1_frame_{i + 1}"] = summary(py[f"x1_{i + 1}"], x1.flat[i])
    worst = max(v["rel_l2"] for k, v in REPORT.items() if k.startswith("x"))
    assert worst < 1e-3
