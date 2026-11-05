"""Monalisa tutorial 1 in Python: coil sensitivity, binning, mitosius, gridded and iterative
reconstructions (Sensa, TevaMorphosia).

Python counterpart of demo/script_demo/script_tutorial_1/*.m (upstream), without display and
without interactive steps:

* raw data readers use ``autoFlag=True`` (no metadata dialogs);
* the normalization ROI drawn with ``roipoly`` in MATLAB is replaced by a centered disk of
  radius N/4 in the central slice (same rule as tools/matlab_capture/scenarios/scenario_tutorial_recon.m);
* both binnings (all lines, sequential 5 s windows) are processed.

The same steps, with explanations and figures: tutorial_1.ipynb in this folder.

Usage (data from demo/data_demo/data_8_tutorial_1/download_data.py)::

    python examples/tutorial_1/tutorial_1.py --data demo/data_demo/data_8_tutorial_1 --out results_py
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

import monalisa as ml
from monalisa.readWrite._mat73 import loadmat73, savemat73


def _log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def coil_sensitivity(data_dir: Path, out_dir: Path) -> np.ndarray:
    """Coil sensitivity maps C (48^3 x nCh) from the body and surface coil scans."""
    body = ml.createRawDataReader(data_dir / "bodyCoil.dat", True)
    head = ml.createRawDataReader(data_dir / "surfaceCoil.dat", True)
    nShotOff = max(body.acquisitionParams.nShot_off, head.acquisitionParams.nShot_off)
    for r in (body, head):
        r.acquisitionParams.nShot_off = nShotOff
        r.acquisitionParams.traj_type = "full_radial3_phylotaxis"
    dK_u = np.array([[1.0, 1.0, 1.0]]) / head.acquisitionParams.FoV
    N_u = np.array([[48.0, 48.0, 48.0]])
    y_body, t, ve = ml.bmCoilSense_nonCart_data(body, N_u)
    y_surface = ml.bmCoilSense_nonCart_data(head, N_u, nargout=1)
    Gn, Gu, Gut = ml.bmTraj2SparseMat(t, ve, N_u, dK_u)
    mask = ml.bmCoilSense_nonCart_mask_automatic(y_body, Gn, True)
    y_ref, C_ref = ml.bmCoilSense_nonCart_ref(y_body, Gn, mask, None)
    C_prime = ml.bmCoilSense_nonCart_primary(y_surface, y_ref, C_ref, Gn, ve, mask)
    C = ml.bmCoilSense_nonCart_secondary(y_surface, C_prime, y_ref, C_ref, Gn, Gu, Gut, ve, 5, False)
    savemat73(out_dir / "coil_sensitivity_map.mat", {"C": C})
    return C


def binnings(reader) -> tuple[np.ndarray, np.ndarray]:
    """All-lines mask (steady state, no self-navigation lines) and sequential 5 s masks."""
    p = reader.acquisitionParams
    nSeg = int(p.nSeg)
    nExclude = int(p.nShot_off) * nSeg
    nLines = int(p.nLine)
    ts = np.ravel(np.asarray(p.timestamp, dtype=np.float64))
    timestampMs = (ts - ts.min()) * 2.5  # Siemens time stamps are in 2.5 ms units
    si = np.arange(0, nLines, nSeg)  # first line of every shot (self navigation)

    allLines = np.ones((1, nLines), dtype=bool)
    allLines[0, :nExclude] = False
    allLines[0, si] = False

    window = 5 * 1000.0
    start = timestampMs[nExclude]
    nMasks = int(np.floor((timestampMs[-1] - start) / window))
    seq = np.zeros((nMasks, nLines), dtype=bool)
    for i in range(nMasks):
        w0 = start + i * window
        m = (timestampMs >= w0) & (timestampMs < w0 + window)
        m[si] = False
        seq[i] = m
    return allLines, seq


def _normalization(x_tot, N):
    """Fixed replacement of the interactive ROI: centered disk of radius N/4, central slice."""
    temp_im = np.abs(x_tot[:, :, N // 2])
    gx, gy = np.meshgrid(np.arange(1, N + 1), np.arange(1, N + 1), indexing="ij")
    roi = (gx - (N / 2 + 1)) ** 2 + (gy - (N / 2 + 1)) ** 2 <= (N / 4) ** 2
    return np.mean(temp_im[roi])


def mitosius(reader, C, masks: dict, out_dir: Path) -> dict:
    """Normalize the raw data and write one mitosius folder per binning."""
    p = reader.acquisitionParams
    p.traj_type = "full_radial3_phylotaxis"
    _log("reading raw data")
    y_tot = reader.readRawData(True, True)
    t_tot = ml.bmTraj(p)
    _log("volume elements")
    ve_tot = ml.bmVolumeElement(t_tot, "voronoi_full_radial3")
    N = int(np.ravel(p.FoV)[0] / 3)
    N_u = np.array([[N, N, N]], dtype=np.float64)
    C = ml.bmImResize(C, [48, 48, 48], N_u)
    _log("gridded reconstruction for normalization")
    x_tot = ml.bmMathilda(y_tot, t_tot, ve_tot, C, N_u, N_u, np.array([[1.0, 1.0, 1.0]]) / 384)
    normalize_val = _normalization(x_tot, N)
    y_tot = y_tot / normalize_val  # single / single, as in MATLAB
    savemat73(out_dir / "mitosius_prep.mat", {"x_tot": x_tot, "normalize_val": np.float32(normalize_val),
                                              "ve_tot": ve_tot})
    nSeg, nShot_off = int(p.nSeg), int(p.nShot_off)
    for name, mask in masks.items():
        _log(f"mitosis {name}")
        m = np.reshape(mask, (mask.shape[0], nSeg, mask.shape[1] // nSeg), order="F")
        m = m[:, 1:, nShot_off:]
        m = ml.bmPointReshape(m)
        y, t = ml.bmMitosis(y_tot, t_tot, m, nargout=2)
        y = ml.bmPermuteToCol(y)
        ve = ml.bmVolumeElement(t, "voronoi_full_radial3")
        ml.bmMitosius_create(str(out_dir / f"mitosius_{name}"), y, t, ve)
    return {"normalize_val": normalize_val, "x_tot": x_tot}


def reconstructions(C, FoV: float, out_dir: Path, nFr: int = 8) -> dict:
    """Gridded reconstructions: all lines (x0) and the first nFr sequential bins (x1)."""
    N = int(FoV / 3)
    N_u = np.array([[N, N, N]], dtype=np.float64)
    dK_u = np.array([[1.0, 1.0, 1.0]]) / FoV
    C = ml.bmImResize(C, [48, 48, 48], N_u)
    d = str(out_dir / "mitosius_allLines")
    y, t, ve = (ml.bmMitosius_load(d, k) for k in ("y", "t", "ve"))
    x0 = ml.bmMathilda(y.flat[0], t.flat[0], ve.flat[0], C, N_u, N_u, dK_u)
    d = str(out_dir / "mitosius_sequential")
    y, t, ve = (ml.bmMitosius_load(d, k) for k in ("y", "t", "ve"))
    x1 = [ml.bmMathilda(y.flat[i], t.flat[i], ve.flat[i], C, N_u, N_u, dK_u) for i in range(nFr)]
    savemat73(out_dir / "reconstructions.mat", {"x0": x0, **{f"x1_{i + 1}": x for i, x in enumerate(x1)}})
    return {"x0": x0, "x1": x1}


def iterative_reconstructions(C, FoV: float, x1: list, out_dir: Path) -> dict:
    """Iterative SENSE (bmSensa, per bin) and compressed sensing with temporal total variation
    (bmTevaMorphosia_chain) of the first len(x1) sequential bins, started from the gridded x1.
    Parameters of reconstructions_script.m: 30 iterations, 4 CG steps, delta 0.1, rho 1."""
    from monalisa.optim.bmWitnessInfo import bmWitnessInfo

    nFr = len(x1)
    N = int(FoV / 3)
    N_u = np.array([[N, N, N]], dtype=np.float64)
    n_u = N_u
    dK_u = np.array([[1.0, 1.0, 1.0]]) / FoV
    C = ml.bmImResize(C, [48, 48, 48], N_u)
    d = str(out_dir / "mitosius_sequential")
    y, t, ve = (ml.bmMitosius_load(d, k)[:nFr] for k in ("y", "t", "ve"))  # cells (nBin, 1)
    Gu, Gut = ml.bmTraj2SparseMat(t, ve, N_u, dK_u, nargout=2)
    nIter, nCGD = 30, 4
    witness_ind = np.arange(1, nIter + 1, 3)
    ve_max = 10 * np.prod(dK_u)

    def witness(name):  # witness files go to out_dir, not the working directory
        w = bmWitnessInfo(name, witness_ind)
        w.out_dir = str(out_dir)
        return w

    x_sensa = [ml.bmSensa(x1[i], y[i, 0], ve[i, 0], C, Gu[i, 0], Gut[i, 0], n_u, nCGD, ve_max, nIter,
                          witness(f"sensa_frame_{i + 1}")) for i in range(nFr)]
    x1_cell = np.empty((nFr, 1), dtype=object)
    for i in range(nFr):
        x1_cell[i, 0] = x1[i]
    delta = 0.1
    rho = 10 * delta
    x_cs = ml.bmTevaMorphosia_chain(x1_cell, None, None, y, ve, C, Gu, Gut, n_u, None, None, delta, rho, "normal",
                                    nCGD, ve_max, nIter, witness("tevaMorphosia_d0p1_r1_nCGD4"))
    x_cs = [x_cs[i, 0] for i in range(nFr)]
    savemat73(out_dir / "iterative.mat", {**{f"x_sensa_{i + 1}": x for i, x in enumerate(x_sensa)},
                                          **{f"x_cs_{i + 1}": x for i, x in enumerate(x_cs)}})
    return {"x_sensa": x_sensa, "x_cs": x_cs}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, required=True,
                    help="folder with bodyCoil.dat, surfaceCoil.dat, brainScan.dat")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--coil-map", type=Path, default=None,
                    help="reuse a coil_sensitivity_map.mat (variable C)")
    ap.add_argument("--skip-iterative", action="store_true",
                    help="only the gridded reconstructions (no Sensa / TevaMorphosia)")
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    if args.coil_map is not None:
        C = loadmat73(args.coil_map)["C"]
    else:
        _log("coil sensitivity")
        C = coil_sensitivity(args.data, args.out)
    _log("binnings")
    reader = ml.createRawDataReader(args.data / "brainScan.dat", True)
    allLines, seq = binnings(reader)
    savemat73(args.out / "binning.mat", {"allLinesMask": allLines, "sequentialMask": seq})
    mitosius(reader, C, {"allLines": allLines, "sequential": seq}, args.out)
    _log("reconstructions")
    FoV = float(np.ravel(reader.acquisitionParams.FoV)[0])
    rec = reconstructions(C, FoV, args.out)
    if not args.skip_iterative:
        _log("iterative reconstructions (Sensa, TevaMorphosia)")
        iterative_reconstructions(C, FoV, rec["x1"], args.out)
    _log(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
