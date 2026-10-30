"""Port of src/fourier123/prep_function/bmFC_conj.m."""

import numpy as np

from monalisa._mat import double, int32, isempty, single, vec
from monalisa.arrayUtility.bmColReshape import bmColReshape


def bmFC_conj(C_conj, N_u, n_u, dK_u):
    """Fourier scaling ``1/prod(dK_u)`` times ``C_conj``, column format, single."""
    if isempty(n_u):
        n_u = N_u
    C_conj = single(C_conj)
    n_u = double(int32(vec(n_u)))
    dK_u = double(single(vec(dK_u)))
    F_conj = np.float32(1 / np.prod(dK_u))
    return single(F_conj * single(bmColReshape(C_conj, n_u)))
