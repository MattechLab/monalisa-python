"""Port of src/fourier123/prep_function/bmKF_conj.m."""

import numpy as np

from monalisa._mat import isempty, single, vec
from monalisa.array._block_reshape import block_reshape
from monalisa.array._col_reshape import col_reshape
from monalisa.fourier._deapodization import deapodization
from monalisa.image._im_crop import im_crop
from monalisa.util._default_kernel import default_kernel


def kf_conj(C_conj, N_u, n_u, dK_u, nCh, kernelType=None, nWin=None, kernelParam=None):
    """Deapodization times ``1/prod(dK_u)`` (times ``C_conj`` when given), for the
    adjoint operator; column format ``[prod(n_u), nCh]``, single."""
    kernelType, nWin, kernelParam = default_kernel(kernelType, nWin, kernelParam)
    C_conj = None if isempty(C_conj) else single(block_reshape(C_conj, n_u))
    N_u = single(vec(N_u))
    n_u = single(vec(n_u))
    dK_u = single(vec(dK_u))
    K = single(deapodization(N_u, dK_u, single(nCh), kernelType, single(vec(nWin)), single(vec(kernelParam))))
    K = im_crop(K, N_u, n_u)
    K = single(col_reshape(K, n_u))
    F_conj = np.float32(1.0 / np.float64(np.prod(dK_u)))
    if C_conj is None:
        return single(K * F_conj)
    C_conj = single(col_reshape(C_conj, n_u))
    return single(K * F_conj * C_conj)
