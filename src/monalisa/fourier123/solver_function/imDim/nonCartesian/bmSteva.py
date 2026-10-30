"""Port of src/fourier123/solver_function/imDim/nonCartesian/bmSteva.m."""

import numpy as np

from monalisa._mat import double, int32, isempty, single, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.fourier123.map_function.nonCartesian.bmNakatsha import bmNakatsha
from monalisa.fourier123.map_function.nonCartesian.bmShanna import bmShanna
from monalisa.fourier123.prep_function.bmKF import bmKF
from monalisa.fourier123.prep_function.bmKF_conj import bmKF_conj
from monalisa.fourier123.solver_function.imDim.nonCartesian._common import dot, inv_single, regul_param, sq
from monalisa.linSpace.bmProx_oneNorm import bmProx_oneNorm
from monalisa.linSpace.bmY_ve_reshape import bmY_ve_reshape
from monalisa.optim.bmBackGradient import bmBackGradient
from monalisa.optim.bmBackGradientT import bmBackGradientT
from monalisa.optim.bmWitnessInfo import cell_row_set, cell_set


def bmSteva(x, z, u, y, ve, C, Gu, Gut, frSize, delta, rho, nCGD, ve_max, nIter, witnessInfo):
    """Total-variation regularized reconstruction (ADMM: ``nCGD`` conjugate
    gradient steps for ``x``, soft thresholding for ``z``, dual update ``u``)."""
    myEps = np.float32(10 * np.finfo(np.float32).eps)
    y = single(y)
    nCh = y.shape[1]
    N_u = double(int32(vec(Gu.N_u)))
    frSize = N_u if isempty(frSize) else double(vec(frSize))
    nPt_u = int(np.prod(frSize))
    imDim = N_u.size
    dK_u = double(single(vec(Gu.d_u)))
    dX_u = single((np.float32(1) / single(dK_u)) / single(N_u))
    if isempty(ve_max):
        ve_max = np.max(ve)
    delta = regul_param(delta, nIter)
    rho = regul_param(rho, nIter)
    HX = np.float32(np.prod(dX_u))
    HZ = HX
    HY = np.minimum(single(bmY_ve_reshape(ve, np.shape(y))), np.float32(ve_max))
    C = single(bmColReshape(C, N_u))
    kp = (Gu.kernel_type, Gu.nWin, Gu.kernelParam)
    KFC = single(bmKF(C, N_u, frSize, dK_u, nCh, *kp))
    KFC_conj = single(bmKF_conj(np.conj(C), N_u, frSize, dK_u, nCh, *kp))
    x = single(bmColReshape(x, frSize))
    z = bmBackGradient(x, frSize, dX_u) if isempty(z) else z
    u = np.zeros((nPt_u, imDim), dtype=np.complex64) if isempty(u) else u
    inv_HX = inv_single(HX)

    for k, (name, val) in enumerate([("recon_name", "steva"), ("dK_u", dK_u), ("N_u", N_u), ("frSize", frSize),
                                     ("delta", delta), ("rho", rho), ("nIter", nIter), ("nCGD", nCGD),
                                     ("ve_max", ve_max), ("residu", np.zeros((1, int(nIter)))),
                                     ("total_variation", np.zeros((1, int(nIter))))], start=1):
        cell_set(witnessInfo.param_name, k, name)
        cell_set(witnessInfo.param, k, val)

    def M(v):
        return bmShanna(v, Gu, KFC, frSize, "MATLAB")

    def dagM(r):
        return inv_HX * bmNakatsha(HY * r, Gut, KFC_conj, True, frSize, "MATLAB")

    def G(v):
        return bmBackGradient(v, frSize, dX_u)

    c = 0
    for c in range(1, int(nIter) + 1):
        rc = rho[0, c - 1]
        res_y_next = y - M(x)
        res_z_next = (z - u) - G(x)
        dagA_res_next = dagM(res_y_next) + rc * inv_HX * bmBackGradientT(HZ * res_z_next, frSize, dX_u)
        p_next = dagA_res_next
        sqn_next = np.real(dot(dagA_res_next, HX * dagA_res_next))
        for i in range(1, int(nCGD) + 1):
            res_y_curr, res_z_curr, sqn_curr, p_curr = res_y_next, res_z_next, sqn_next, p_next
            if sqn_curr < myEps:
                break
            Mp = M(p_curr)
            Fp = G(p_curr)
            a = sqn_curr / (sq(Mp, HY) + sq(Fp, rc * HZ))
            x = x + a * p_curr
            if i == nCGD:
                break
            res_y_next = res_y_curr - a * Mp
            res_z_next = res_z_curr - a * Fp
            dagA_res_next = dagM(res_y_next) + rc * inv_HX * bmBackGradientT(HZ * res_z_next, frSize, dX_u)
            sqn_next = np.real(dot(dagA_res_next, HX * dagA_res_next))
            b = sqn_next / sqn_curr
            p_next = dagA_res_next + b * p_curr
        bGx_plus_u = G(x) + u
        z = bmProx_oneNorm(bGx_plus_u, delta[0, c - 1] / rc)
        u = bGx_plus_u - z
        temp_r = y - M(x)
        R = sq(temp_r, HY)
        g = G(x)
        TV = HZ * np.sum(np.abs(np.real(g))) + HZ * np.sum(np.abs(np.imag(g)))
        cell_row_set(witnessInfo.param, 9, c, R)  # upstream indices (9, 10), one below the init
        cell_row_set(witnessInfo.param, 10, c, TV)
        witnessInfo.watch(c, x, frSize, "loop")
    witnessInfo.watch(c, x, frSize, "final")
    return bmBlockReshape(x, frSize)
