"""Port of src/fourier123/prep_function/bmFC.m."""

import numpy as np

from monalisa._mat import double, int32, isempty, single, vec
from monalisa.array._col_reshape import col_reshape


def fc(C, N_u, n_u, dK_u):
    """Fourier scaling ``1/prod(N_u)/prod(dK_u)`` times ``C``, column format, single."""
    if isempty(n_u):
        n_u = N_u
    C = single(C)
    N_u = double(int32(vec(N_u)))
    n_u = double(int32(vec(n_u)))
    dK_u = double(single(vec(dK_u)))
    F = np.float32(1 / np.prod(N_u) / np.prod(dK_u))
    return single(F * single(col_reshape(C, n_u)))
