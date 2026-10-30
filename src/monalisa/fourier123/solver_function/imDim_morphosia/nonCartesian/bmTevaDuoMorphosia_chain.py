"""Port of src/fourier123/solver_function/imDim_morphosia/nonCartesian/bmTevaDuoMorphosia_chain.m."""

import numpy as np

from monalisa._mat import cell_from_items, cell_items, disp, double, int32, isempty, single, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.arrayUtility.bmSingle import bmSingle
from monalisa.arrayUtility.bmZero import bmZero
from monalisa.fourier123.map_function.nonCartesian.bmNakatsha import bmNakatsha
from monalisa.fourier123.map_function.nonCartesian.bmShanna import bmShanna
from monalisa.fourier123.prep_function.bmKF import bmKF
from monalisa.fourier123.prep_function.bmKF_conj import bmKF_conj
from monalisa.fourier123.solver_function.imDim.nonCartesian._common import inv_single, regul_param
from monalisa.image123.bmImDeform import bmImDeform
from monalisa.image123.bmImDeformT import bmImDeformT
from monalisa.linSpace.bmProx_oneNorm import bmProx_oneNorm
from monalisa.linSpace.bmY_ve_reshape import bmY_ve_reshape
from monalisa.mathOp.bmAxpy import bmAxpy
from monalisa.mathOp.bmMinus import bmMinus
from monalisa.mathOp.bmMult import bmMult
from monalisa.mathOp.bmPlus import bmPlus
from monalisa.mathOp.bmSquaredNorm import bmSquaredNorm
from monalisa.optim.bmInitialWitnessInfo import bmInitialWitnessInfo
from monalisa.optim.bmWitnessInfo import cell_row_set


def bmTevaDuoMorphosia_chain(x, z1, z2, u1, u2, y, ve, C, Gu, Gut, frSize, Tu1, Tu1t, Tu2, Tu2t, delta, rho,
                             regul_mode, nCGD, ve_max, nIter, witnessInfo, *, nargout=1):
    """Chain reconstruction with temporal total variation toward both the previous
    (``Tu1``) and the next (``Tu2``) frame. Returns ``x`` or, with ``nargout``,
    ``(x, z1, z2, u1, u2)``."""
    label = "tevaDuoMorphosia"
    disp(f"{label} initial...")
    myEps = np.float32(10 * np.finfo(np.float32).eps)
    x = bmSingle(bmColReshape(x, frSize))
    y = bmSingle(y)
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
    HY = [np.minimum(single(bmY_ve_reshape(v, np.shape(yi))), np.float32(ve_max))
          for v, yi in zip(cell_items(ve), ys, strict=True)]
    delta_list = regul_param(delta, nIter)
    rho_list = regul_param(rho, nIter)
    C = single(bmBlockReshape(C, frSize))
    kp = (Gus[0].kernel_type, Gus[0].nWin, Gus[0].kernelParam)
    KFC = single(bmKF(C, N_u, frSize, dK_u, nCh, *kp))
    KFC_conj = single(bmKF_conj(np.conj(C), N_u, frSize, dK_u, nCh, *kp))

    def items(T):
        return [None] * nFr if isempty(T) else cell_items(T)

    T1, T1t, T2, T2t = items(Tu1), items(Tu1t), items(Tu2), items(Tu2t)
    K_bump = None
    inv_HX = inv_single(HX)
    half_inv_HX = np.float32(0.5 / np.float64(HX))

    def cells(lst):
        return cell_from_items(lst, (nFr, 1))

    def M(v):
        return cells([bmShanna(xi, G, KFC, frSize, "MATLAB") for xi, G in zip(cell_items(v), Gus, strict=True)])

    def F1(v):
        xs = cell_items(v)
        return cells([0.5 * (bmImDeform(T1[i], xs[i], frSize, K_bump) - xs[(i - 1) % nFr]) for i in range(nFr)])

    def F2(v):
        xs = cell_items(v)
        return cells([0.5 * (bmImDeform(T2[i], xs[i], frSize, K_bump) - xs[(i + 1) % nFr]) for i in range(nFr)])

    def dagM(r):
        rs = cell_items(r)
        return cells([inv_HX * bmNakatsha(HY[i] * rs[i], Guts[i], KFC_conj, True, frSize, "MATLAB")
                      for i in range(nFr)])

    def dagF1(r):
        zs = cell_items(r)
        return cells([half_inv_HX * (bmImDeformT(T1t[i], HZ1 * zs[i], frSize, K_bump) - HZ1 * zs[(i + 1) % nFr])
                      for i in range(nFr)])

    def dagF2(r):
        zs = cell_items(r)
        return cells([half_inv_HX * (bmImDeformT(T2t[i], HZ2 * zs[i], frSize, K_bump) - HZ2 * zs[(i - 1) % nFr])
                      for i in range(nFr)])

    def l1(r, h):
        return h * np.sum(np.abs(np.real(r))) + h * np.sum(np.abs(np.imag(r)))

    def dafi_regul(v):
        xs = cell_items(v)
        dafi = 0
        regul = 0
        for i in range(nFr):
            dafi = dafi + bmSquaredNorm(ys[i] - bmShanna(xs[i], Gus[i], KFC, frSize, "MATLAB"), HY[i])
            regul = regul + l1(xs[(i - 1) % nFr] - bmImDeform(T1[i], xs[i], frSize, K_bump), HZ1)
            regul = regul + l1(xs[(i + 1) % nFr] - bmImDeform(T2[i], xs[i], frSize, K_bump), HZ2)
        return dafi, regul

    z1 = F1(x) if isempty(z1) else z1
    z2 = F2(x) if isempty(z2) else z2
    u1 = bmZero([nPt_u, 1], "complex_single", [nFr, 1]) if isempty(u1) else u1
    u2 = bmZero([nPt_u, 1], "complex_single", [nFr, 1]) if isempty(u2) else u2
    bmInitialWitnessInfo(witnessInfo, label, N_u, frSize, dK_u, ve_max, nIter, nCGD, delta_list, rho_list,
                         regul_mode)
    dafi, regul = dafi_regul(x)
    disp("... initial done. ")
    disp(f"{label} is running ...")

    def dagA(ry, rz1, rz2):
        return bmPlus(dagM(ry), bmPlus(bmMult(rho_c, dagF1(rz1)), bmMult(rho_c, dagF2(rz2))))

    c = 0
    for c in range(1, int(nIter) + 1):
        if regul_mode == "normal":
            delta_c, rho_c = delta_list[0, c - 1], rho_list[0, c - 1]
        else:
            delta_c = delta_list[0, c - 1] * regul / dafi
            rho_c = rho_list[0, c - 1] * delta_c
        res_y = bmMinus(y, M(x))
        res_z1 = bmMinus(bmMinus(z1, u1), F1(x))
        res_z2 = bmMinus(bmMinus(z2, u2), F2(x))
        dagA_res_next = dagA(res_y, res_z1, res_z2)
        p_next = dagA_res_next
        sqn_next = bmSquaredNorm(dagA_res_next, HX)
        for j in range(1, int(nCGD) + 1):
            sqn_curr, p_curr = sqn_next, p_next
            if sqn_curr < myEps:
                break
            Mp, F1p, F2p = M(p_curr), F1(p_curr), F2(p_curr)
            sqn_Ap = bmSquaredNorm(Mp, HY) + bmSquaredNorm(F1p, rho_c * HZ1) + bmSquaredNorm(F2p, rho_c * HZ2)
            a = sqn_curr / sqn_Ap
            x = bmAxpy(a, p_curr, x)
            if j == nCGD:
                break
            res_y = bmAxpy(-a, Mp, res_y)
            res_z1 = bmAxpy(-a, F1p, res_z1)
            res_z2 = bmAxpy(-a, F2p, res_z2)
            dagA_res_next = dagA(res_y, res_z1, res_z2)
            sqn_next = bmSquaredNorm(dagA_res_next, HX)
            b = sqn_next / sqn_curr
            p_next = bmAxpy(b, p_curr, dagA_res_next)
        F1x_plus_u1 = bmPlus(u1, F1(x))
        F2x_plus_u2 = bmPlus(u2, F2(x))
        z1 = bmProx_oneNorm(F1x_plus_u1, delta_c / rho_c)
        z2 = bmProx_oneNorm(F2x_plus_u2, delta_c / rho_c)
        u1 = bmMinus(F1x_plus_u1, z1)
        u2 = bmMinus(F2x_plus_u2, z2)
        dafi, regul = dafi_regul(x)
        cell_row_set(witnessInfo.param, 11, c, 0.5 * dafi + 0.5 * delta_c * regul)
        cell_row_set(witnessInfo.param, 12, c, dafi)
        cell_row_set(witnessInfo.param, 13, c, regul)
        witnessInfo.watch(c, x, frSize, "loop")
    disp(f"... {label} completed. ")
    witnessInfo.watch(c, x, frSize, "final")
    x = bmBlockReshape(x, frSize)
    out = (x, z1, z2, u1, u2)
    return x if nargout <= 1 else out[:nargout]
