"""Port of src/fourier123/solver_function/imDim_morphosia/nonCartesian/bmSensitivaMorphosia_chain.m."""

import numpy as np

from monalisa._mat import cell_from_items, cell_items, disp, double, int32, isempty, single, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.arrayUtility.bmSingle import bmSingle
from monalisa.fourier123.map_function.nonCartesian.bmNakatsha import bmNakatsha
from monalisa.fourier123.map_function.nonCartesian.bmShanna import bmShanna
from monalisa.fourier123.prep_function.bmKF import bmKF
from monalisa.fourier123.prep_function.bmKF_conj import bmKF_conj
from monalisa.fourier123.solver_function.imDim.nonCartesian._common import inv_single, regul_param
from monalisa.image123.bmImDeform import bmImDeform
from monalisa.image123.bmImDeformT import bmImDeformT
from monalisa.linSpace.bmY_ve_reshape import bmY_ve_reshape
from monalisa.mathOp.bmAxpy import bmAxpy
from monalisa.mathOp.bmMinus import bmMinus
from monalisa.mathOp.bmMult import bmMult
from monalisa.mathOp.bmPlus import bmPlus
from monalisa.mathOp.bmSquaredNorm import bmSquaredNorm
from monalisa.optim.bmInitialWitnessInfo import bmInitialWitnessInfo
from monalisa.optim.bmWitnessInfo import cell_row_set


def bmSensitivaMorphosia_chain(x, y, ve, C, Gu, Gut, frSize, Tu, Tut, delta, regul_mode, nCGD, ve_max, nIter,
                               witnessInfo):
    """Chain reconstruction with a quadratic (L2) penalty on the differences
    between consecutive (optionally motion-compensated) frames, by restarted
    conjugate gradient; ``regul_mode`` ``'normal'`` or ``'adapt'``."""
    label = "sensitivaMorphosia"
    disp(f"{label} initial...")
    myEps = np.float32(10 * np.finfo(np.float32).eps)
    x = bmSingle(bmColReshape(x, frSize))
    y = bmSingle(y)
    ys, Gus, Guts = cell_items(y), cell_items(Gu), cell_items(Gut)
    nFr = len(ys)
    nCh = ys[0].shape[1]
    N_u = double(int32(vec(Gus[0].N_u)))
    frSize = double(int32(vec(frSize)))
    dK_u = single(vec(Gus[0].d_u))
    dX_u = single((np.float32(1) / single(dK_u)) / single(N_u))
    HX = np.float32(np.prod(dX_u))
    HZ = HX
    HY = [np.minimum(single(bmY_ve_reshape(v, np.shape(yi))), np.float32(ve_max))
          for v, yi in zip(cell_items(ve), ys, strict=True)]
    delta_list = regul_param(delta, nIter)
    C = single(bmBlockReshape(C, frSize))
    kp = (Gus[0].kernel_type, Gus[0].nWin, Gus[0].kernelParam)
    KFC = single(bmKF(C, N_u, frSize, dK_u, nCh, *kp))
    KFC_conj = single(bmKF_conj(np.conj(C), N_u, frSize, dK_u, nCh, *kp))
    Tus = [None] * nFr if isempty(Tu) else cell_items(Tu)
    Tuts = [None] * nFr if isempty(Tut) else cell_items(Tut)
    K_bump = None
    inv_HX = inv_single(HX)

    def cells(lst):
        return cell_from_items(lst, (nFr, 1))

    def M(v):
        return cells([bmShanna(xi, G, KFC, frSize, "MATLAB") for xi, G in zip(cell_items(v), Gus, strict=True)])

    def F(v):
        xs = cell_items(v)
        return cells([bmImDeform(Tus[i], xs[i], frSize, K_bump) - xs[(i - 1) % nFr] for i in range(nFr)])

    def dagM(r):
        rs = cell_items(r)
        return cells([inv_HX * bmNakatsha(HY[i] * rs[i], Guts[i], KFC_conj, True, frSize, "MATLAB")
                      for i in range(nFr)])

    def dagF(r):
        zs = cell_items(r)
        return cells([inv_HX * (bmImDeformT(Tuts[i], HZ * zs[i], frSize, K_bump) - HZ * zs[(i + 1) % nFr])
                      for i in range(nFr)])

    def dafi_regul(v):
        xs = cell_items(v)
        dafi = 0
        regul = 0
        for i in range(nFr):
            dafi = dafi + bmSquaredNorm(ys[i] - bmShanna(xs[i], Gus[i], KFC, frSize, "MATLAB"), HY[i])
            regul = regul + bmSquaredNorm(xs[(i - 1) % nFr] - bmImDeform(Tus[i], xs[i], frSize, K_bump), HZ)
        return dafi, regul

    bmInitialWitnessInfo(witnessInfo, label, N_u, frSize, dK_u, ve_max, nIter, nCGD, delta_list, None, regul_mode)
    dafi, regul = dafi_regul(x)
    disp("... initial done. ")
    disp(f"{label} is running ...")
    c = 0
    for c in range(1, int(nIter) + 1):
        if regul_mode == "normal":
            delta_c = delta_list[0, c - 1]
        else:
            delta_c = delta_list[0, c - 1] * regul / dafi
        res_y = bmMinus(y, M(x))
        res_z = bmMinus(0, F(x))
        dagA_res_next = bmPlus(dagM(res_y), bmMult(delta_c, dagF(res_z)))
        p_next = dagA_res_next
        sqn_next = bmSquaredNorm(dagA_res_next, HX)
        for j in range(1, int(nCGD) + 1):
            sqn_curr, p_curr = sqn_next, p_next
            if sqn_curr < myEps:
                break
            Mp = M(p_curr)
            Fp = F(p_curr)
            a = sqn_curr / (bmSquaredNorm(Mp, HY) + bmSquaredNorm(Fp, delta_c * HZ))
            x = bmAxpy(a, p_curr, x)
            if j == nCGD:
                break
            res_y = bmAxpy(-a, Mp, res_y)
            res_z = bmAxpy(-a, Fp, res_z)
            dagA_res_next = bmPlus(dagM(res_y), bmMult(delta_c, dagF(res_z)))
            sqn_next = bmSquaredNorm(dagA_res_next, HX)
            b = sqn_next / sqn_curr
            p_next = bmAxpy(b, p_curr, dagA_res_next)
        dafi, regul = dafi_regul(x)
        cell_row_set(witnessInfo.param, 11, c, 0.5 * dafi + 0.5 * delta_c * regul)
        cell_row_set(witnessInfo.param, 12, c, dafi)
        cell_row_set(witnessInfo.param, 13, c, regul)
        witnessInfo.watch(c, x, frSize, "loop")
    disp(f"... {label} completed. ")
    witnessInfo.watch(c, x, frSize, "final")
    return bmBlockReshape(x, frSize)
