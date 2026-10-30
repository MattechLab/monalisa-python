"""Port of src/coilSense/map/bmCoilSense_pinv.m."""

import numpy as np

from monalisa._mat import single
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape


def bmCoilSense_pinv(C, x0, n_u):
    """Coil combination ``sum(conj(C) .* x0, 2) ./ sum(abs(C).^2, 2)`` in single precision."""
    C = single(bmColReshape(C, n_u))
    x0 = single(bmColReshape(x0, n_u))
    with np.errstate(divide="ignore", invalid="ignore"):
        x = np.sum(np.conj(C) * x0, axis=1, keepdims=True) / np.sum(np.abs(C) ** 2, axis=1, keepdims=True)
    return bmBlockReshape(x, n_u)
