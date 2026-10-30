"""Port of src/imageN/bmRMS.m."""

import numpy as np

from monalisa._mat import squeeze
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.arrayUtility.bmIsBlockShape import bmIsBlockShape
from monalisa.arrayUtility.bmIsColShape import bmIsColShape


def bmRMS(x, N_u):
    """Root mean square over the channels."""
    c = bmColReshape(x, N_u)
    a = squeeze(np.sqrt(np.mean(np.abs(c) ** 2, axis=1, keepdims=True)))
    if bmIsColShape(x, N_u):
        a = bmColReshape(a, N_u)
    elif bmIsBlockShape(x, N_u):
        a = bmBlockReshape(a, N_u)
    return a
