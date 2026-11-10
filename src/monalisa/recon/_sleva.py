"""Port of src/fourier123/solver_function/imDim/nonCartesian/bmSleva.m."""

import numpy as np

from monalisa._mat import disp, double, int32, single, vec
from monalisa.array._block_reshape import block_reshape
from monalisa.array._col_reshape import col_reshape
from monalisa.array._to_single import to_single
from monalisa.fourier._kf import kf
from monalisa.fourier._kf_conj import kf_conj
from monalisa.fourier._nakatsha import nakatsha
from monalisa.fourier._shanna import shanna
from monalisa.optim._axpy import axpy
from monalisa.optim._initial_witness_info import initial_witness_info
from monalisa.optim._minus import minus
from monalisa.optim._mult import mult
from monalisa.optim._plus import plus
from monalisa.optim._squared_norm import squared_norm
from monalisa.optim._witness_info import cell_row_set
from monalisa.optim._y_ve_reshape import y_ve_reshape
from monalisa.recon._common import inv_single, regul_param


def sleva(x, y, ve, C, Gu, Gut, frSize, delta, regul_mode, nCGD, ve_max, nIter, witnessInfo):
    """L2 (Tikhonov) regularized reconstruction by restarted conjugate gradient;
    ``regul_mode`` ``'normal'`` (fixed ``delta``) or ``'adapt'``."""
    label = "sleva"
    disp(f"{label} initial...")
    myEps = np.float32(10 * np.finfo(np.float32).eps)
    x = to_single(col_reshape(x, frSize))
    y = to_single(y)
    nCh = y.shape[1]
    N_u = double(int32(vec(Gu.N_u)))
    frSize = double(int32(vec(frSize)))
    dK_u = single(vec(Gu.d_u))
    dX_u = single((np.float32(1) / single(dK_u)) / single(N_u))
    HX = np.float32(np.prod(dX_u))
    HZ = HX
    HY = np.minimum(single(y_ve_reshape(ve, np.shape(y))), np.float32(ve_max))
    delta_list = regul_param(delta, nIter)
    C = single(block_reshape(C, frSize))
    kp = (Gu.kernel_type, Gu.nWin, Gu.kernelParam)
    KFC = single(kf(C, N_u, frSize, dK_u, nCh, *kp))
    KFC_conj = single(kf_conj(np.conj(C), N_u, frSize, dK_u, nCh, *kp))
    initial_witness_info(witnessInfo, label, N_u, frSize, dK_u, ve_max, nIter, nCGD, delta_list, None, regul_mode)
    inv_HX = inv_single(HX)

    def M(v):
        return shanna(v, Gu, KFC, frSize, "MATLAB")

    def dagM(r):
        return inv_HX * nakatsha(HY * r, Gut, KFC_conj, True, frSize, "MATLAB")

    def dafi_regul(v):
        return squared_norm(y - M(v), HY), squared_norm(v, HZ)

    dafi, regul = dafi_regul(x)
    disp("... initial done. ")
    disp(f"{label} is running ...")
    c = 0
    for c in range(1, int(nIter) + 1):
        if regul_mode == "normal":
            delta = delta_list[0, c - 1]
        elif regul_mode == "adapt":
            delta = delta_list[0, c - 1] * regul / dafi
        res_y_next = minus(y, M(x))
        res_z_next = minus(0, x)
        dagA_res_next = plus(dagM(res_y_next), mult(delta, res_z_next))
        p_next = dagA_res_next
        sqn_next = squared_norm(dagA_res_next, HX)
        for j in range(1, int(nCGD) + 1):
            res_y_curr, res_z_curr, sqn_curr, p_curr = res_y_next, res_z_next, sqn_next, p_next
            if sqn_curr < myEps:
                break
            Mp = M(p_curr)
            Fp = p_curr
            a = sqn_curr / (squared_norm(Mp, HY) + squared_norm(Fp, delta * HZ))
            x = axpy(a, p_curr, x)
            if j == nCGD:
                break
            res_y_next = axpy(-a, Mp, res_y_curr)
            res_z_next = axpy(-a, Fp, res_z_curr)
            dagA_res_next = plus(dagM(res_y_next), mult(delta, res_z_next))
            sqn_next = squared_norm(dagA_res_next, HX)
            b = sqn_next / sqn_curr
            p_next = axpy(b, p_curr, dagA_res_next)
        dafi, regul = dafi_regul(x)
        cell_row_set(witnessInfo.param, 11, c, 0.5 * dafi + 0.5 * delta * regul)
        cell_row_set(witnessInfo.param, 12, c, dafi)
        cell_row_set(witnessInfo.param, 13, c, regul)
        witnessInfo.watch(c, x, frSize, "loop")
    disp(f"... {label} completed. ")
    witnessInfo.watch(c, x, frSize, "final")
    return block_reshape(x, frSize)
