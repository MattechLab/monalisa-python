"""Port of src/fourier123/prep_function/bmKF.m."""

import numpy as np

from monalisa._mat import isempty, single, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.fourier123.prep_function.bmK import bmK
from monalisa.image123.bmImCrope import bmImCrope
from monalisa.varargin.bmVarargin_kernelType_nWin_kernelParam import (
    bmVarargin_kernelType_nWin_kernelParam,
)


def bmKF(C, N_u, n_u, dK_u, nCh, kernelType=None, nWin=None, kernelParam=None):
    """Deapodization times Fourier scaling ``1/prod(N_u)/prod(dK_u)`` (times ``C``
    when given), column format ``[prod(n_u), nCh]``, single."""
    kernelType, nWin, kernelParam = bmVarargin_kernelType_nWin_kernelParam(kernelType, nWin, kernelParam)
    C = None if isempty(C) else single(bmBlockReshape(C, n_u))
    N_u = single(vec(N_u))
    n_u = single(vec(n_u))
    dK_u = single(vec(dK_u))
    K = single(bmK(N_u, dK_u, single(nCh), kernelType, single(vec(nWin)), single(vec(kernelParam))))
    K = bmImCrope(K, N_u, n_u)
    K = single(bmColReshape(K, n_u))
    F = np.float32(np.float32(1.0 / np.float64(np.prod(N_u))) / np.prod(dK_u))
    if C is None:
        return single(K * F)
    C = single(bmColReshape(C, n_u))
    return single(K * F * C)
