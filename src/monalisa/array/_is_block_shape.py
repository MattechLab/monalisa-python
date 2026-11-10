"""Port of src/arrayUtility/bmIsBlockShape.m."""

import numpy as np

from monalisa._mat import msize, numel, vec


def is_block_shape(x, N_u):
    """True when ``size(x)`` equals ``[N_u, nCh]`` exactly (MATLAB ``isequal``)."""
    N_u = vec(N_u)
    nCh = numel(x) / np.prod(N_u)
    myBlockSize = [*N_u, nCh]
    return len(msize(x)) == len(myBlockSize) and all(
        float(a) == float(b) for a, b in zip(msize(x), myBlockSize, strict=True)
    )
