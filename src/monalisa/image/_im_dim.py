"""Port of src/imageN/bmImDim.m."""

import numpy as np

from monalisa._mat import msize


def im_dim(a, nargout=2):
    """Image dimension ``n`` (vectors are 1D, empty is 0) and size ``s``;
    with ``nargout`` up to 5 also ``sx, sy, sz`` (``None`` when absent)."""
    s = msize(a)
    n = len(s)
    if n == 2:
        n = 0 if min(s) == 0 else (1 if min(s) == 1 else 2)
    sx = float(s[0]) if n > 0 else None
    sy = float(s[1]) if n > 1 else None
    sz = float(s[2]) if n > 2 else None
    out = (float(n), np.array([s], dtype=np.float64), sx, sy, sz)
    return out[0] if nargout <= 1 else out[:nargout]
