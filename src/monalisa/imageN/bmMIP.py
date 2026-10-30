"""Port of src/imageN/bmMIP.m."""

import numpy as np

from monalisa._mat import squeeze
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.arrayUtility.bmIsBlockShape import bmIsBlockShape
from monalisa.arrayUtility.bmIsColShape import bmIsColShape


def bmMIP(y, N_u):
    """Maximum intensity projection over the channels."""
    c = bmColReshape(y, N_u)
    a = squeeze(np.max(np.abs(c), axis=1, keepdims=True))
    if bmIsColShape(y, N_u):
        a = bmColReshape(a, N_u)
    elif bmIsBlockShape(y, N_u):
        a = bmBlockReshape(a, N_u)
    return a
