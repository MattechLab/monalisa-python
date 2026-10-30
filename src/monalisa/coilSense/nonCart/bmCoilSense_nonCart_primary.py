"""Port of src/coilSense/nonCart/bmCoilSense_nonCart_primary.m."""

import numpy as np

from monalisa._mat import mixed, msize, numel, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmCol import bmCol
from monalisa.fourier123.map_function.nonCartesian.bmNasha import bmNasha
from monalisa.image123.bmImLaplaceEquationSolver import bmImLaplaceEquationSolver
from monalisa.image123.bmImPseudoDiffusion_inMask import bmImPseudoDiffusion_inMask
from monalisa.linSpace.bmY_norm import bmY_norm


def bmCoilSense_nonCart_primary(y, y_ref, C_ref, Gn, ve, m):
    """First estimate of the coil sensitivities of the array ``y`` relative to
    the reference coil (``y_ref``, ``C_ref``), smoothed in the mask ``m`` and
    harmonically extended outside."""
    nIter_smooth = 2
    L_nIter = 1000
    L_th = 1e-4
    N_u = vec(Gn.N_u)
    shape = [int(n) for n in N_u]
    nPt = int(Gn.r_size)
    nCh = int(numel(y) / nPt)
    nCh_array = msize(y, 2)
    y = np.asarray(y)
    norm_ref = bmY_norm(y_ref, ve)
    mean_norm = np.mean(bmCol(bmY_norm(y, ve, False)))
    y_ref = mixed(np.multiply, np.asarray(y_ref), nCh_array) / norm_ref * mean_norm
    x_ref = bmBlockReshape(bmNasha(y_ref, Gn, N_u), N_u)
    x = np.reshape(bmNasha(y, Gn, N_u), [*shape, nCh], order="F")
    m = np.reshape(np.asarray(m, dtype=bool), shape, order="F")
    m_neg = ~m
    with np.errstate(divide="ignore", invalid="ignore"):
        anat_ref = x_ref / C_ref
    anat_ref[m_neg] = 1
    C = np.zeros([*shape, nCh], dtype=np.complex64, order="F")
    for i in range(nCh):
        with np.errstate(divide="ignore", invalid="ignore"):
            temp_im = bmImPseudoDiffusion_inMask(x[..., i] / anat_ref, m, nIter_smooth)
        temp_im[m_neg] = 0
        C[..., i] = bmImLaplaceEquationSolver(temp_im, m, L_nIter, L_th, "omp")
    C = mixed(np.multiply, C, nCh_array)
    return bmBlockReshape(C, N_u)
