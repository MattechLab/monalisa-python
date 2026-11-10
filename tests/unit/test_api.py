"""Public API: names, subpackages and the MATLAB -> Python renaming table."""

import inspect
import re
import sys
from pathlib import Path

import monalisa

TOOLS = Path(__file__).parents[2] / "tools"
sys.path.insert(0, str(TOOLS))
import renaming_table  # noqa: E402

SUBPACKAGES = ["array", "binning", "coil", "display", "fourier", "geometry", "gridding", "image", "io", "optim",
               "recon", "registration", "sparse", "trajectory", "util"]


def _public():
    return [n for n in monalisa.__all__ if n not in SUBPACKAGES and n not in ("MATLAB_NAMES", "UPSTREAM_COMMIT")]


def test_every_matlab_name_resolves():
    for matlab, target in monalisa.MATLAB_NAMES.items():
        package, name = target.split(".")
        obj = monalisa.find_function(matlab)
        assert obj is getattr(monalisa, name), matlab
        assert obj.__name__ == name and name in getattr(monalisa, package).__all__, matlab
    assert monalisa.find_function("bmNotPorted") is None


def test_public_names_follow_pep8_without_author_prefix():
    names = _public()
    assert len(names) == len(set(names))
    for n in names:
        obj = getattr(monalisa, n)
        assert not renaming_table.AUTHOR_PREFIX.match(n), n
        if inspect.isclass(obj):
            assert re.fullmatch(r"[A-Z][A-Za-z0-9]*", n), n
        else:
            assert re.fullmatch(r"[a-z][a-z0-9_]*", n), n
    for package in SUBPACKAGES:  # every subpackage exports what it lists, from private modules
        mod = getattr(monalisa, package)
        for n in mod.__all__:
            assert getattr(mod, n).__module__.startswith(f"monalisa.{package}._"), (package, n)
            assert n in monalisa.__all__, n


def test_naming_rule():
    rule = renaming_table.python_name
    assert rule("bmMathilda") == "mathilda"
    assert rule("bmCoilSense_nonCart_data") == "coil_sense_non_cart_data"
    assert rule("bmTraj2SparseMat") == "traj_to_sparse_mat"
    assert rule("bmGridder_n2u_leight") == "gridder_n2u_leight"
    assert rule("thresholdRMS_MIP") == "threshold_rms_mip"
    assert rule("bmIDF1_conjTrans") == "idf1_conj_trans"
    assert rule("mleSiemensReader", is_class=True) == "SiemensReader"


def test_renaming_table_is_up_to_date():
    # rows() raises if a name departs from the rule without a reason
    current = (TOOLS.parent / "docs" / "renaming.md").read_text()
    assert current == renaming_table.render(), "run python tools/renaming_table.py"
