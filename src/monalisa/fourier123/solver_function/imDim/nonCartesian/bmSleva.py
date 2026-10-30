"""Port of src/fourier123/solver_function/imDim/nonCartesian/bmSleva.m."""

import numpy as np

from monalisa._mat import disp, double, int32, single, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.arrayUtility.bmSingle import bmSingle
from monalisa.fourier123.map_function.nonCartesian.bmNakatsha import bmNakatsha
from monalisa.fourier123.map_function.nonCartesian.bmShanna import bmShanna
from monalisa.fourier123.prep_function.bmKF import bmKF
from monalisa.fourier123.prep_function.bmKF_conj import bmKF_conj
from monalisa.fourier123.solver_function.imDim.nonCartesian._common import inv_single, regul_param
from monalisa.linSpace.bmY_ve_reshape import bmY_ve_reshape
from monalisa.mathOp.bmAxpy import bmAxpy
from monalisa.mathOp.bmMinus import bmMinus
from monalisa.mathOp.bmMult import bmMult
from monalisa.mathOp.bmPlus import bmPlus
from monalisa.mathOp.bmSquaredNorm import bmSquaredNorm
from monalisa.optim.bmInitialWitnessInfo import bmInitialWitnessInfo
from monalisa.optim.bmWitnessInfo import cell_row_set


def bmSleva(x, y, ve, C, Gu, Gut, frSize, delta, regul_mode, nCGD, ve_max, nIter, witnessInfo):
    """L2 (Tikhonov) regularized reconstruction by restarted conjugate gradient;
    ``regul_mode`` ``'normal'`` (fixed ``delta``) or ``'adapt'``."""
    label = "sleva"
    disp(f"{label} initial...")
    myEps = np.float32(10 * np.finfo(np.float32).eps)
    x = bmSingle(bmColReshape(x, frSize))
    y = bmSingle(y)
    nCh = y.shape[1]
    N_u = double(int32(vec(Gu.N_u)))
    frSize = double(int32(vec(frSize)))
    dK_u = single(vec(Gu.d_u))
    dX_u = single((np.float32(1) / single(dK_u)) / single(N_u))
    HX = np.float32(np.prod(dX_u))
    HZ = HX
    HY = np.minimum(single(bmY_ve_reshape(ve, np.shape(y))), np.float32(ve_max))
    delta_list = regul_param(delta, nIter)
    C = single(bmBlockReshape(C, frSize))
    kp = (Gu.kernel_type, Gu.nWin, Gu.kernelParam)
    KFC = single(bmKF(C, N_u, frSize, dK_u, nCh, *kp))
    KFC_conj = single(bmKF_conj(np.conj(C), N_u, frSize, dK_u, nCh, *kp))
    bmInitialWitnessInfo(witnessInfo, label, N_u, frSize, dK_u, ve_max, nIter, nCGD, delta_list, None, regul_mode)
    inv_HX = inv_single(HX)

    def M(v):
        return bmShanna(v, Gu, KFC, frSize, "MATLAB")

    def dagM(r):
        return inv_HX * bmNakatsha(HY * r, Gut, KFC_conj, True, frSize, "MATLAB")

    def dafi_regul(v):
        return bmSquaredNorm(y - M(v), HY), bmSquaredNorm(v, HZ)

    dafi, regul = dafi_regul(x)
    disp("... initial done. ")
    disp(f"{label} is running ...")
    c = 0
    for c in range(1, int(nIter) + 1):
        if regul_mode == "normal":
            delta = delta_list[0, c - 1]
        elif regul_mode == "adapt":
            delta = delta_list[0, c - 1] * regul / dafi
        res_y_next = bmMinus(y, M(x))
        res_z_next = bmMinus(0, x)
        dagA_res_next = bmPlus(dagM(res_y_next), bmMult(delta, res_z_next))
        p_next = dagA_res_next
        sqn_next = bmSquaredNorm(dagA_res_next, HX)
        for j in range(1, int(nCGD) + 1):
            res_y_curr, res_z_curr, sqn_curr, p_curr = res_y_next, res_z_next, sqn_next, p_next
            if sqn_curr < myEps:
                break
            Mp = M(p_curr)
            Fp = p_curr
            a = sqn_curr / (bmSquaredNorm(Mp, HY) + bmSquaredNorm(Fp, delta * HZ))
            x = bmAxpy(a, p_curr, x)
            if j == nCGD:
                break
            res_y_next = bmAxpy(-a, Mp, res_y_curr)
            res_z_next = bmAxpy(-a, Fp, res_z_curr)
            dagA_res_next = bmPlus(dagM(res_y_next), bmMult(delta, res_z_next))
            sqn_next = bmSquaredNorm(dagA_res_next, HX)
            b = sqn_next / sqn_curr
            p_next = bmAxpy(b, p_curr, dagA_res_next)
        dafi, regul = dafi_regul(x)
        cell_row_set(witnessInfo.param, 11, c, 0.5 * dafi + 0.5 * delta * regul)
        cell_row_set(witnessInfo.param, 12, c, dafi)
        cell_row_set(witnessInfo.param, 13, c, regul)
        witnessInfo.watch(c, x, frSize, "loop")
    disp(f"... {label} completed. ")
    witnessInfo.watch(c, x, frSize, "final")
    return bmBlockReshape(x, frSize)
