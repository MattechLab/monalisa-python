"""Port of src/fourier123/solver_function/imDim_morphosia/nonCartesian/bmTevaDuoMorphosia_chain.m."""

import numpy as np

from monalisa._mat import cell_from_items, cell_items, disp, double, int32, isempty, single, vec
from monalisa.array._block_reshape import block_reshape
from monalisa.array._col_reshape import col_reshape
from monalisa.array._to_single import to_single
from monalisa.array._zero import zero
from monalisa.fourier._kf import kf
from monalisa.fourier._kf_conj import kf_conj
from monalisa.fourier._nakatsha import nakatsha
from monalisa.fourier._shanna import shanna
from monalisa.image._im_deform import im_deform
from monalisa.image._im_deform_t import im_deform_t
from monalisa.optim._axpy import axpy
from monalisa.optim._initial_witness_info import initial_witness_info
from monalisa.optim._minus import minus
from monalisa.optim._mult import mult
from monalisa.optim._plus import plus
from monalisa.optim._prox_one_norm import prox_one_norm
from monalisa.optim._squared_norm import squared_norm
from monalisa.optim._witness_info import cell_row_set
from monalisa.optim._y_ve_reshape import y_ve_reshape
from monalisa.recon._common import inv_single, regul_param


def teva_duo_morphosia_chain(x, z1, z2, u1, u2, y, ve, C, Gu, Gut, frSize, Tu1, Tu1t, Tu2, Tu2t, delta, rho,
                             regul_mode, nCGD, ve_max, nIter, witnessInfo, *, nargout=1):
    """Chain reconstruction with temporal total variation toward both the previous
    (``Tu1``) and the next (``Tu2``) frame. Returns ``x`` or, with ``nargout``,
    ``(x, z1, z2, u1, u2)``."""
    label = "tevaDuoMorphosia"
    disp(f"{label} initial...")
    myEps = np.float32(10 * np.finfo(np.float32).eps)
    x = to_single(col_reshape(x, frSize))
    y = to_single(y)
    ys, Gus, Guts = cell_items(y), cell_items(Gu), cell_items(Gut)
    nFr = len(ys)
    nCh = ys[0].shape[1]
    N_u = double(int32(vec(Gus[0].N_u)))
    frSize = double(int32(vec(frSize)))
    nPt_u = int(np.prod(frSize))
    dK_u = single(vec(Gus[0].d_u))
    dX_u = single((np.float32(1) / single(dK_u)) / single(N_u))
    HX = np.float32(np.prod(dX_u))
    HZ1 = HX
    HZ2 = HX
    HY = [np.minimum(single(y_ve_reshape(v, np.shape(yi))), np.float32(ve_max))
          for v, yi in zip(cell_items(ve), ys, strict=True)]
    delta_list = regul_param(delta, nIter)
    rho_list = regul_param(rho, nIter)
    C = single(block_reshape(C, frSize))
    kp = (Gus[0].kernel_type, Gus[0].nWin, Gus[0].kernelParam)
    KFC = single(kf(C, N_u, frSize, dK_u, nCh, *kp))
    KFC_conj = single(kf_conj(np.conj(C), N_u, frSize, dK_u, nCh, *kp))

    def items(T):
        return [None] * nFr if isempty(T) else cell_items(T)

    T1, T1t, T2, T2t = items(Tu1), items(Tu1t), items(Tu2), items(Tu2t)
    K_bump = None
    inv_HX = inv_single(HX)
    half_inv_HX = np.float32(0.5 / np.float64(HX))

    def cells(lst):
        return cell_from_items(lst, (nFr, 1))

    def M(v):
        return cells([shanna(xi, G, KFC, frSize, "MATLAB") for xi, G in zip(cell_items(v), Gus, strict=True)])

    def F1(v):
        xs = cell_items(v)
        return cells([0.5 * (im_deform(T1[i], xs[i], frSize, K_bump) - xs[(i - 1) % nFr]) for i in range(nFr)])

    def F2(v):
        xs = cell_items(v)
        return cells([0.5 * (im_deform(T2[i], xs[i], frSize, K_bump) - xs[(i + 1) % nFr]) for i in range(nFr)])

    def dagM(r):
        rs = cell_items(r)
        return cells([inv_HX * nakatsha(HY[i] * rs[i], Guts[i], KFC_conj, True, frSize, "MATLAB")
                      for i in range(nFr)])

    def dagF1(r):
        zs = cell_items(r)
        return cells([half_inv_HX * (im_deform_t(T1t[i], HZ1 * zs[i], frSize, K_bump) - HZ1 * zs[(i + 1) % nFr])
                      for i in range(nFr)])

    def dagF2(r):
        zs = cell_items(r)
        return cells([half_inv_HX * (im_deform_t(T2t[i], HZ2 * zs[i], frSize, K_bump) - HZ2 * zs[(i - 1) % nFr])
                      for i in range(nFr)])

    def l1(r, h):
        return h * np.sum(np.abs(np.real(r))) + h * np.sum(np.abs(np.imag(r)))

    def dafi_regul(v):
        xs = cell_items(v)
        dafi = 0
        regul = 0
        for i in range(nFr):
            dafi = dafi + squared_norm(ys[i] - shanna(xs[i], Gus[i], KFC, frSize, "MATLAB"), HY[i])
            regul = regul + l1(xs[(i - 1) % nFr] - im_deform(T1[i], xs[i], frSize, K_bump), HZ1)
            regul = regul + l1(xs[(i + 1) % nFr] - im_deform(T2[i], xs[i], frSize, K_bump), HZ2)
        return dafi, regul

    z1 = F1(x) if isempty(z1) else z1
    z2 = F2(x) if isempty(z2) else z2
    u1 = zero([nPt_u, 1], "complex_single", [nFr, 1]) if isempty(u1) else u1
    u2 = zero([nPt_u, 1], "complex_single", [nFr, 1]) if isempty(u2) else u2
    initial_witness_info(witnessInfo, label, N_u, frSize, dK_u, ve_max, nIter, nCGD, delta_list, rho_list,
                         regul_mode)
    dafi, regul = dafi_regul(x)
    disp("... initial done. ")
    disp(f"{label} is running ...")

    def dagA(ry, rz1, rz2):
        return plus(dagM(ry), plus(mult(rho_c, dagF1(rz1)), mult(rho_c, dagF2(rz2))))

    c = 0
    for c in range(1, int(nIter) + 1):
        if regul_mode == "normal":
            delta_c, rho_c = delta_list[0, c - 1], rho_list[0, c - 1]
        else:
            delta_c = delta_list[0, c - 1] * regul / dafi
            rho_c = rho_list[0, c - 1] * delta_c
        res_y = minus(y, M(x))
        res_z1 = minus(minus(z1, u1), F1(x))
        res_z2 = minus(minus(z2, u2), F2(x))
        dagA_res_next = dagA(res_y, res_z1, res_z2)
        p_next = dagA_res_next
        sqn_next = squared_norm(dagA_res_next, HX)
        for j in range(1, int(nCGD) + 1):
            sqn_curr, p_curr = sqn_next, p_next
            if sqn_curr < myEps:
                break
            Mp, F1p, F2p = M(p_curr), F1(p_curr), F2(p_curr)
            sqn_Ap = squared_norm(Mp, HY) + squared_norm(F1p, rho_c * HZ1) + squared_norm(F2p, rho_c * HZ2)
            a = sqn_curr / sqn_Ap
            x = axpy(a, p_curr, x)
            if j == nCGD:
                break
            res_y = axpy(-a, Mp, res_y)
            res_z1 = axpy(-a, F1p, res_z1)
            res_z2 = axpy(-a, F2p, res_z2)
            dagA_res_next = dagA(res_y, res_z1, res_z2)
            sqn_next = squared_norm(dagA_res_next, HX)
            b = sqn_next / sqn_curr
            p_next = axpy(b, p_curr, dagA_res_next)
        F1x_plus_u1 = plus(u1, F1(x))
        F2x_plus_u2 = plus(u2, F2(x))
        z1 = prox_one_norm(F1x_plus_u1, delta_c / rho_c)
        z2 = prox_one_norm(F2x_plus_u2, delta_c / rho_c)
        u1 = minus(F1x_plus_u1, z1)
        u2 = minus(F2x_plus_u2, z2)
        dafi, regul = dafi_regul(x)
        cell_row_set(witnessInfo.param, 11, c, 0.5 * dafi + 0.5 * delta_c * regul)
        cell_row_set(witnessInfo.param, 12, c, dafi)
        cell_row_set(witnessInfo.param, 13, c, regul)
        witnessInfo.watch(c, x, frSize, "loop")
    disp(f"... {label} completed. ")
    witnessInfo.watch(c, x, frSize, "final")
    x = block_reshape(x, frSize)
    out = (x, z1, z2, u1, u2)
    return x if nargout <= 1 else out[:nargout]
