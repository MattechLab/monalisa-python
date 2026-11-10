"""Port of src/fourier123/prep_function/bmKF.m."""

import numpy as np

from monalisa._mat import isempty, single, vec
from monalisa.array._block_reshape import block_reshape
from monalisa.array._col_reshape import col_reshape
from monalisa.fourier._deapodization import deapodization
from monalisa.image._im_crop import im_crop
from monalisa.util._default_kernel import default_kernel


def kf(C, N_u, n_u, dK_u, nCh, kernelType=None, nWin=None, kernelParam=None):
    """Deapodization times Fourier scaling ``1/prod(N_u)/prod(dK_u)`` (times ``C``
    when given), column format ``[prod(n_u), nCh]``, single."""
    kernelType, nWin, kernelParam = default_kernel(kernelType, nWin, kernelParam)
    C = None if isempty(C) else single(block_reshape(C, n_u))
    N_u = single(vec(N_u))
    n_u = single(vec(n_u))
    dK_u = single(vec(dK_u))
    K = single(deapodization(N_u, dK_u, single(nCh), kernelType, single(vec(nWin)), single(vec(kernelParam))))
    K = im_crop(K, N_u, n_u)
    K = single(col_reshape(K, n_u))
    F = np.float32(np.float32(1.0 / np.float64(np.prod(N_u))) / np.prod(dK_u))
    if C is None:
        return single(K * F)
    C = single(col_reshape(C, n_u))
    return single(K * F * C)
