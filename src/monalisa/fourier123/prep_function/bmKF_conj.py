"""Port of src/fourier123/prep_function/bmKF_conj.m."""

import numpy as np

from monalisa._mat import isempty, single, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.fourier123.prep_function.bmK import bmK
from monalisa.image123.bmImCrope import bmImCrope
from monalisa.varargin.bmVarargin_kernelType_nWin_kernelParam import (
    bmVarargin_kernelType_nWin_kernelParam,
)


def bmKF_conj(C_conj, N_u, n_u, dK_u, nCh, kernelType=None, nWin=None, kernelParam=None):
    """Deapodization times ``1/prod(dK_u)`` (times ``C_conj`` when given), for the
    adjoint operator; column format ``[prod(n_u), nCh]``, single."""
    kernelType, nWin, kernelParam = bmVarargin_kernelType_nWin_kernelParam(kernelType, nWin, kernelParam)
    C_conj = None if isempty(C_conj) else single(bmBlockReshape(C_conj, n_u))
    N_u = single(vec(N_u))
    n_u = single(vec(n_u))
    dK_u = single(vec(dK_u))
    K = single(bmK(N_u, dK_u, single(nCh), kernelType, single(vec(nWin)), single(vec(kernelParam))))
    K = bmImCrope(K, N_u, n_u)
    K = single(bmColReshape(K, n_u))
    F_conj = np.float32(1.0 / np.float64(np.prod(dK_u)))
    if C_conj is None:
        return single(K * F_conj)
    C_conj = single(bmColReshape(C_conj, n_u))
    return single(K * F_conj * C_conj)
