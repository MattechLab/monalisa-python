"""Port of src/coilSense/map/bmCoilSense_pinv.m."""

import numpy as np

from monalisa._mat import single
from monalisa.array._block_reshape import block_reshape
from monalisa.array._col_reshape import col_reshape


def coil_sense_pinv(C, x0, n_u):
    """Coil combination ``sum(conj(C) .* x0, 2) ./ sum(abs(C).^2, 2)`` in single precision."""
    C = single(col_reshape(C, n_u))
    x0 = single(col_reshape(x0, n_u))
    with np.errstate(divide="ignore", invalid="ignore"):
        x = np.sum(np.conj(C) * x0, axis=1, keepdims=True) / np.sum(np.abs(C) ** 2, axis=1, keepdims=True)
    return block_reshape(x, n_u)
