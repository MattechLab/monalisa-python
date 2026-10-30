"""Port of src/coilSense/nonCart/bmCoilSense_nonCart_ref.m."""

import numpy as np

from monalisa._mat import isempty, numel, single, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.fourier123.map_function.nonCartesian.bmNasha import bmNasha
from monalisa.image123.bmImLaplaceEquationSolver import bmImLaplaceEquationSolver
from monalisa.image123.bmImPseudoDiffusion_inMask import bmImPseudoDiffusion_inMask
from monalisa.imageN.bmRMS import bmRMS


def bmCoilSense_nonCart_ref(y, Gn, m, nSmooth_phi=None):
    """Reference coil (first channel of ``y``) and its sensitivity: magnitude
    relative to the RMS image, smoothed in the mask and harmonically extended
    outside. Returns ``(y_ref, C_ref)``."""
    L_nIter = 1000
    L_th = 1e-4
    nIter_smooth = 2
    N_u = vec(Gn.N_u)
    shape = [int(n) for n in N_u]
    nPt = int(Gn.r_size)
    nCh = int(numel(y) / nPt)
    m = np.reshape(np.asarray(m, dtype=bool), shape, order="F")
    m_neg = ~m
    m_neg_rep = np.tile(~np.reshape(m, (-1, 1), order="F"), (1, nCh))

    x_ch = np.array(single(bmColReshape(bmNasha(y, Gn, N_u), N_u)))
    x_ch[m_neg_rep] = 1
    x_ch = bmBlockReshape(x_ch, N_u)
    myRMS = bmRMS(x_ch, N_u)
    C = np.zeros([*shape, nCh], dtype=np.complex64, order="F")
    x_ch = np.reshape(x_ch, [*shape, nCh], order="F")
    for i in range(nCh):
        temp_a = x_ch[..., i]
        C_abs = bmImPseudoDiffusion_inMask(np.abs(temp_a) / myRMS, m, nIter_smooth)
        if not isempty(nSmooth_phi):
            C_phi = np.angle(bmImPseudoDiffusion_inMask(temp_a, m, nSmooth_phi))
        else:
            C_phi = np.zeros(temp_a.shape)
        temp_C = (C_abs * np.exp(1j * C_phi)).astype(np.complex64)
        temp_C[m_neg] = 0
        C[..., i] = bmImLaplaceEquationSolver(temp_C, m, L_nIter, L_th, "omp")
    C = bmColReshape(C, N_u)
    C_ref = bmBlockReshape(C[:, 0:1], N_u)
    y_ref = np.asarray(y)[:, 0:1]
    return y_ref, C_ref
