"""Port of src/fourier123/solver_function/imDim/nonCartesian/bmSensa.m."""

import numpy as np

from monalisa._mat import double, isempty, single, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.fourier123.map_function.nonCartesian.bmNakatsha import bmNakatsha
from monalisa.fourier123.map_function.nonCartesian.bmShanna import bmShanna
from monalisa.fourier123.prep_function.bmKF import bmKF
from monalisa.fourier123.prep_function.bmKF_conj import bmKF_conj
from monalisa.fourier123.solver_function.imDim.nonCartesian._common import dot, inv_single, sq
from monalisa.linSpace.bmY_ve_reshape import bmY_ve_reshape
from monalisa.optim.bmWitnessInfo import cell_row_set, cell_set


def bmSensa(x, y, ve, C, Gu, Gut, frSize, nCGD, ve_max, nIter, witnessInfo):
    """SENSE reconstruction: ``nIter`` restarts of ``nCGD`` conjugate gradient
    steps on the density-weighted least squares data fidelity, from ``x``."""
    myEps = np.float32(10 * np.finfo(np.float32).eps)
    y = single(y)
    nCh = y.shape[1]
    N_u = double(single(vec(Gu.N_u)))
    frSize = double(single(vec(frSize)))
    dK_u = double(single(vec(Gu.d_u)))
    C = single(bmColReshape(C, N_u))
    ve = single(bmY_ve_reshape(ve, y.shape))
    kp = (Gu.kernel_type, Gu.nWin, Gu.kernelParam)
    KFC = single(bmColReshape(bmKF(C, N_u, frSize, dK_u, nCh, *kp), frSize))
    KFC_conj = single(bmColReshape(bmKF_conj(np.conj(C), N_u, frSize, dK_u, nCh, *kp), frSize))
    x = single(bmColReshape(x, frSize))
    dX_u = single((np.float32(1) / single(dK_u)) / single(N_u))
    HX = np.prod(dX_u)
    if isempty(ve_max):
        ve_max = np.max(ve)
    HY = np.minimum(ve, np.float32(ve_max))
    inv_HX = inv_single(HX)

    for k, (name, val) in enumerate([("recon_name", "sensa"), ("dK_u", dK_u), ("N_u", N_u), ("frSize", frSize),
                                     ("nIter", nIter), ("nCGD", nCGD), ("ve_max", ve_max),
                                     ("residu", np.zeros((1, int(nIter))))], start=1):
        cell_set(witnessInfo.param_name, k, name)
        cell_set(witnessInfo.param, k, val)

    def M(v):
        return bmShanna(v, Gu, KFC, frSize, "MATLAB")

    def dagM(r):
        return inv_HX * bmNakatsha(HY * r, Gut, KFC_conj, True, frSize, "MATLAB")

    c = 0
    for c in range(1, int(nIter) + 1):
        res_next = y - M(x)
        dagM_res_next = dagM(res_next)
        sqn_next = np.real(dot(dagM_res_next, HX * dagM_res_next))
        p_next = dagM_res_next
        for i in range(1, int(nCGD) + 1):
            res_curr, sqn_curr, p_curr = res_next, sqn_next, p_next
            if sqn_curr < myEps:
                break
            Mp = M(p_curr)
            a = sqn_curr / sq(Mp, HY)
            x = x + a * p_curr
            if i == nCGD:
                break
            res_next = res_curr - a * Mp
            dagM_res_next = dagM(res_next)
            sqn_next = np.real(dot(dagM_res_next, HX * dagM_res_next))
            b = sqn_next / sqn_curr
            p_next = dagM_res_next + b * p_curr
        temp_r = y - M(x)
        cell_row_set(witnessInfo.param, 7, c, sq(temp_r, HY))  # upstream writes the residual into param{7}
        witnessInfo.watch(c, x, frSize, "loop")
    witnessInfo.watch(c, x, frSize, "final")
    return bmBlockReshape(x, frSize)
