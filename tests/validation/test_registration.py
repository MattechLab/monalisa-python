"""Validation of the demons registration replacement and of the motion-compensated reconstructions.

MATLAB's ``imregdemons`` is replaced by SimpleITK's demons (monalisa.imReg._demons), so the
deformation fields are compared on quality, not to rounding. Opt-in (needs the MATLAB references
of tools/matlab_capture/validation and the upstream demo data):

    matlab -batch "addpath('tools/matlab_capture/validation'); \
        imregdemons_reference('fixtures/validation/imregdemons_reference.mat'); \
        registration_reference('fixtures/validation', '/path/to/monalisa')"
    MONALISA_UPSTREAM=/path/to/monalisa pytest tests/validation -s

A report is written to fixtures/validation/registration_report.json (see
docs/validation_registration.md).
"""

import json
import os
from pathlib import Path

import numpy as np
import pytest
import scipy.io as sio

pytest.importorskip("SimpleITK")

from monalisa.readWrite._mat73 import loadmat73  # noqa: E402
from monalisa.testing.metrics import rel_l2, summary  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
VAL = ROOT / "fixtures" / "validation"
UPSTREAM = os.environ.get("MONALISA_UPSTREAM")
REPORT = {}


@pytest.fixture(scope="module", autouse=True)
def write_report():
    yield
    if REPORT:
        (VAL / "registration_report.json").write_text(json.dumps(REPORT, indent=1))
        print(json.dumps(REPORT, indent=1))


def _xy_to_axes(D):
    d = D.copy()
    d[..., 0], d[..., 1] = D[..., 1], D[..., 0]
    return d


def _field_stats(v_py, v_ml, weight_mask=None):
    """Endpoint error between two displacement fields ``[..., dim]`` (pixels)."""
    epe = np.sqrt(((v_py - v_ml) ** 2).sum(-1))
    mag = np.sqrt((v_ml**2).sum(-1))
    if weight_mask is not None:
        epe, mag = epe[weight_mask], mag[weight_mask]
    return {"epe_mean": float(epe.mean()), "epe_p95": float(np.percentile(epe, 95)),
            "ref_disp_mean": float(mag.mean()), "ref_disp_max": float(mag.max()),
            "rel_l2": float(np.linalg.norm(epe) / np.linalg.norm(mag))}


# ------------------------------------------------------------------------------ imregdemons itself

@pytest.mark.skipif(not (VAL / "imregdemons_reference.mat").exists(), reason="run imregdemons_reference.m first")
def test_imregdemons_vs_matlab():
    from monalisa.imReg._demons import imregdemons

    cases = sio.loadmat(VAL / "imregdemons_reference.mat", squeeze_me=True, struct_as_record=False)["cases"]
    for c in cases:
        D, moving_reg = imregdemons(c.moving, c.fixed, np.atleast_1d(c.iterations))
        g = np.sqrt(sum(gi**2 for gi in np.gradient(c.fixed.astype(float))))
        structure = g > 0.05 * g.max()  # where the images constrain the field
        inner = tuple(slice(4, n - 4) for n in c.fixed.shape)
        before = rel_l2(c.moving[inner], c.fixed[inner])
        r = {"field": _field_stats(_xy_to_axes(D), _xy_to_axes(c.D), structure),
             "image_error_before": before,
             "image_error_matlab": rel_l2(c.moving_reg[inner], c.fixed[inner]),
             "image_error_python": rel_l2(moving_reg[inner], c.fixed[inner])}
        REPORT[f"imregdemons/{c.name}"] = r
        assert r["image_error_python"] < 0.6 * before
        assert r["image_error_python"] < 1.5 * r["image_error_matlab"] + 0.02
        assert r["field"]["epe_mean"] < 0.6


# ------------------------------------------------------------------------------ chain (demo data 5)

needs_chain = pytest.mark.skipif(
    UPSTREAM is None or not (VAL / "chain_data5.mat").exists(),
    reason="set MONALISA_UPSTREAM and run registration_reference.m first",
)


@pytest.fixture(scope="module")
def chain():
    import monalisa as ml
    from monalisa.optim.bmWitnessInfo import bmWitnessInfo

    S = sio.loadmat(Path(UPSTREAM) / "demo" / "data_demo" / "data_5_chain_radial_simulated_from_cartesian" / "data.mat")
    t, y = S["t"], S["y"]
    N_u, dK_u, frSize = S["N_u"], S["dK_u"], S["frSize"]
    nFr = int(S["nFr"].item())
    ve = ml.bmVolumeElement(t, "voronoi_full_radial2")
    C_size = np.array(S["C"].shape[: int(S["frDim"].item())], float)[None, :]
    C = ml.bmImResize(S["C"], C_size, frSize)
    x0 = np.empty((nFr, 1), dtype=object)
    for i in range(nFr):
        x0[i, 0] = ml.bmMathilda(y[i, 0], t[i, 0], ve[i, 0], C, N_u, frSize, dK_u, None, None, None, None)
    _, Gu, Gut = ml.bmTraj2SparseMat(t, ve, N_u, dK_u, nargout=3)
    ve_max = 10 * np.prod(dK_u)

    def solve(name, Tu1, Tu1t, Tu2=None, Tu2t=None):
        w = bmWitnessInfo(name, None, False)
        if name == "teva":
            return ml.bmTevaMorphosia_chain(x0, None, None, y, ve, C, Gu, Gut, frSize, Tu1, Tu1t, 0.3, 3, "normal",
                                            4, ve_max, 30, w)
        if name == "duo":
            return ml.bmTevaDuoMorphosia_chain(x0, None, None, None, None, y, ve, C, Gu, Gut, frSize,
                                               Tu1, Tu1t, Tu2, Tu2t, 0.3, 3, "normal", 4, ve_max, 30, w)
        return ml.bmSensitivaMorphosia_chain(x0, y, ve, C, Gu, Gut, frSize, Tu1, Tu1t, 3, "normal",
                                             4, ve_max, 30, w)

    x1 = ml.bmTevaMorphosia_chain(x0, None, None, y, ve, C, Gu, Gut, frSize, None, None, 0.1, 1, "normal",
                                  4, ve_max, 30, bmWitnessInfo("teva", None, False))
    return {"S": S, "x0": x0, "x1": x1, "N_u": N_u, "frSize": frSize, "solve": solve,
            "ref": loadmat73(VAL / "chain_data5.mat")}


def _stack(c):
    return np.stack([np.asarray(a) for a in np.asarray(c, dtype=object).flat], axis=-1)


@needs_chain
def test_chain_reconstructions_without_registration(chain, tmp_path, monkeypatch):
    ref = chain["ref"]
    REPORT["chain/x0_mathilda"] = summary(_stack(chain["x0"]), _stack(ref["x0"]))
    REPORT["chain/x1_tevaMorphosia_noDF"] = summary(_stack(chain["x1"]), _stack(ref["x1"]))
    assert REPORT["chain/x0_mathilda"]["rel_l2"] < 1e-4
    assert REPORT["chain/x1_tevaMorphosia_noDF"]["rel_l2"] < 1e-3


@pytest.fixture(scope="module")
def chain_fields(chain):
    import monalisa as ml

    ref = chain["ref"]
    reg_mask = chain["S"]["reg_mask"]
    out = {}
    for name, kind in (("DF_to_prev", "curr_to_prev"), ("DF_to_next", "curr_to_next")):
        # registration of the MATLAB images, to compare the fields on identical inputs
        out[name] = ml.bmImDeformFieldChain_imRegDemons23(ref["x1"], chain["frSize"], kind, 500, 1, None,
                                                          reg_mask, 10, nargout=2)
    return out


@needs_chain
def test_chain_fields_vs_matlab(chain, chain_fields):
    ref = chain["ref"]
    mask = chain["S"]["reg_mask"].astype(bool).ravel(order="F")
    for name in ("DF_to_prev", "DF_to_next"):
        DF_py, im_py = chain_fields[name]
        DF_ml, im_ml = ref[name], ref["imReg_" + name[3:]]
        v_py = np.concatenate([np.asarray(v).T[mask] for v in DF_py.flat])
        v_ml = np.concatenate([np.asarray(v).T[mask] for v in np.asarray(DF_ml, dtype=object).flat])
        REPORT[f"chain/{name}"] = _field_stats(v_py, v_ml)
        REPORT[f"chain/{name}_registered_images"] = summary(_stack(im_py), _stack(im_ml))
        assert REPORT[f"chain/{name}"]["rel_l2"] < 0.5


@needs_chain
@pytest.mark.parametrize("solver", ["teva", "duo", "sens"])
def test_motion_compensated_reconstructions(chain, chain_fields, solver, tmp_path, monkeypatch):
    """The solvers with MATLAB's fields (port validation) and with the Python fields (end to end)."""
    import monalisa as ml

    monkeypatch.chdir(tmp_path)
    ref = chain["ref"]
    x_ml = _stack(ref[{"teva": "x_teva_DF", "duo": "x_duo_DF", "sens": "x_sens_DF"}[solver]])
    N_u = chain["N_u"]
    for src, DF_prev, DF_next in (("matlab_fields", ref["DF_to_prev"], ref["DF_to_next"]),
                                  ("python_fields", chain_fields["DF_to_prev"][0], chain_fields["DF_to_next"][0])):
        Tu1, Tu1t = ml.bmImDeformField2SparseMat(DF_prev, N_u, None, True)
        Tu2, Tu2t = ml.bmImDeformField2SparseMat(DF_next, N_u, None, True) if solver == "duo" else (None, None)
        x_py = _stack(chain["solve"](solver, Tu1, Tu1t, Tu2, Tu2t))
        REPORT[f"chain/x_{solver}_DF/{src}"] = summary(x_py, x_ml)
    # reference scale: how much the deformation fields change the reconstruction at all
    REPORT[f"chain/x_{solver}_DF/effect_of_fields_vs_noDF_x1"] = summary(_stack(ref["x1"]), x_ml)
    assert REPORT[f"chain/x_{solver}_DF/matlab_fields"]["rel_l2"] < 1e-3
    assert REPORT[f"chain/x_{solver}_DF/python_fields"]["ssim"] > 0.95


# ------------------------------------------------------------------------------ sheet (demo data 7)

@pytest.mark.skipif(not (VAL / "sheet_data7.mat").exists(), reason="run registration_reference.m first")
@pytest.mark.skipif(UPSTREAM is None, reason="set MONALISA_UPSTREAM")
def test_sheet_fields_vs_matlab():
    import monalisa as ml

    ref = loadmat73(VAL / "sheet_data7.mat")
    S = sio.loadmat(Path(UPSTREAM) / "demo" / "data_demo" / "data_7_sheet_radial_simulated_from_XCAT" / "data.mat",
                    variable_names=["frSize", "reg_mask"])
    DF1, DF2 = ml.bmImDeformFieldSheet_imRegDemons23(ref["xs0"], S["frSize"], "curr_to_prev", [100, 100], 1, None,
                                                     S["reg_mask"], 10)
    mask = S["reg_mask"].astype(bool).ravel(order="F")
    for name, py in (("DF_sheet_1", DF1), ("DF_sheet_2", DF2)):
        v_py = np.concatenate([np.asarray(v).T[mask] for v in py.flat])
        v_ml = np.concatenate([np.asarray(v).T[mask] for v in np.asarray(ref[name], dtype=object).flat])
        REPORT[f"sheet/{name}"] = _field_stats(v_py, v_ml)
        assert REPORT[f"sheet/{name}"]["rel_l2"] < 0.5
