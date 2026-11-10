"""Port of src/arrayUtility/bmIsColShape.m."""

import numpy as np

from monalisa._mat import msize, numel, vec


def is_col_shape(x, N_u):
    """True when ``size(x)`` equals ``[prod(N_u), nCh]`` exactly (MATLAB ``isequal``)."""
    N_u = vec(N_u)
    nCh = numel(x) / np.prod(N_u)
    myColSize = [np.prod(N_u), nCh]
    return len(msize(x)) == 2 and all(
        float(a) == float(b) for a, b in zip(msize(x), myColSize, strict=True)
    )
