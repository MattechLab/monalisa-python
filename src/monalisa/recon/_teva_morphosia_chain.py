"""Port of src/fourier123/solver_function/imDim_morphosia/nonCartesian/bmTevaMorphosia_chain.m."""

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


def teva_morphosia_chain(x, z, u, y, ve, C, Gu, Gut, frSize, Tu, Tut, delta, rho, regul_mode, nCGD, ve_max, nIter,
                         witnessInfo):
    """Reconstruction of a chain of frames with temporal total variation between
    consecutive frames (optionally motion compensated by the deformation matrices
    ``Tu``/``Tut``), by ADMM with ``nCGD`` conjugate gradient steps per iteration.
    ``x``, ``y``, ``ve``, ``Gu``, ``Gut`` (and ``Tu``, ``Tut``) are cells over frames."""
    label = "tevaMorphosia"
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
    HZ = HX
    HY = [np.minimum(single(y_ve_reshape(v, np.shape(yi))), np.float32(ve_max))
          for v, yi in zip(cell_items(ve), ys, strict=True)]
    delta_list = regul_param(delta, nIter)
    rho_list = regul_param(rho, nIter)
    C = single(block_reshape(C, frSize))
    kp = (Gus[0].kernel_type, Gus[0].nWin, Gus[0].kernelParam)
    KFC = single(kf(C, N_u, frSize, dK_u, nCh, *kp))
    KFC_conj = single(kf_conj(np.conj(C), N_u, frSize, dK_u, nCh, *kp))
    Tus = [None] * nFr if isempty(Tu) else cell_items(Tu)
    Tuts = [None] * nFr if isempty(Tut) else cell_items(Tut)
    K_bump = None
    inv_HX = inv_single(HX)

    def cells(items):
        return cell_from_items(items, (nFr, 1))

    def M(v):
        return cells([shanna(xi, G, KFC, frSize, "MATLAB") for xi, G in zip(cell_items(v), Gus, strict=True)])

    def F(v):
        xs = cell_items(v)
        return cells([im_deform(Tus[i], xs[i], frSize, K_bump) - xs[(i - 1) % nFr] for i in range(nFr)])

    def dagM(r):
        rs = cell_items(r)
        return cells([inv_HX * nakatsha(HY[i] * rs[i], Guts[i], KFC_conj, True, frSize, "MATLAB")
                      for i in range(nFr)])

    def dagF(r):
        zs = cell_items(r)
        return cells([inv_HX * (im_deform_t(Tuts[i], HZ * zs[i], frSize, K_bump) - HZ * zs[(i + 1) % nFr])
                      for i in range(nFr)])

    def dafi_regul(v):
        xs = cell_items(v)
        dafi = 0
        regul = 0
        for i in range(nFr):
            dafi = dafi + squared_norm(ys[i] - shanna(xs[i], Gus[i], KFC, frSize, "MATLAB"), HY[i])
            r = xs[(i - 1) % nFr] - im_deform(Tus[i], xs[i], frSize, K_bump)
            regul = regul + HZ * np.sum(np.abs(np.real(r))) + HZ * np.sum(np.abs(np.imag(r)))
        return dafi, regul

    if isempty(z):
        z = F(x)
    if isempty(u):
        u = zero([nPt_u, 1], "complex_single", [nFr, 1])
    initial_witness_info(witnessInfo, label, N_u, frSize, dK_u, ve_max, nIter, nCGD, delta_list, rho_list,
                         regul_mode)
    dafi, regul = dafi_regul(x)
    disp("... initial done. ")
    disp(f"{label} is running ...")
    c = 0
    for c in range(1, int(nIter) + 1):
        if regul_mode == "normal":
            delta_c, rho_c = delta_list[0, c - 1], rho_list[0, c - 1]
        else:
            delta_c = delta_list[0, c - 1] * regul / dafi
            rho_c = rho_list[0, c - 1] * delta_c
        res_y_next = minus(y, M(x))
        res_z_next = minus(minus(z, u), F(x))
        dagA_res_next = plus(dagM(res_y_next), mult(rho_c, dagF(res_z_next)))
        p_next = dagA_res_next
        sqn_next = squared_norm(dagA_res_next, HX)
        for j in range(1, int(nCGD) + 1):
            res_y_curr, res_z_curr, sqn_curr, p_curr = res_y_next, res_z_next, sqn_next, p_next
            if sqn_curr < myEps:
                break
            Mp = M(p_curr)
            Fp = F(p_curr)
            a = sqn_curr / (squared_norm(Mp, HY) + squared_norm(Fp, rho_c * HZ))
            x = axpy(a, p_curr, x)
            if j == nCGD:
                break
            res_y_next = axpy(-a, Mp, res_y_curr)
            res_z_next = axpy(-a, Fp, res_z_curr)
            dagA_res_next = plus(dagM(res_y_next), mult(rho_c, dagF(res_z_next)))
            sqn_next = squared_norm(dagA_res_next, HX)
            b = sqn_next / sqn_curr
            p_next = axpy(b, p_curr, dagA_res_next)
        Fx_plus_u = plus(u, F(x))
        z = prox_one_norm(Fx_plus_u, delta_c / rho_c)
        u = minus(Fx_plus_u, z)
        dafi, regul = dafi_regul(x)
        cell_row_set(witnessInfo.param, 11, c, 0.5 * dafi + 0.5 * delta_c * regul)
        cell_row_set(witnessInfo.param, 12, c, dafi)
        cell_row_set(witnessInfo.param, 13, c, regul)
        witnessInfo.watch(c, x, frSize, "loop")
    disp(f"... {label} completed. ")
    witnessInfo.watch(c, x, frSize, "final")
    return block_reshape(x, frSize)
