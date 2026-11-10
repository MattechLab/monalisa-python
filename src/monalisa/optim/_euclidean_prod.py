"""Port of src/mathOp/bmEuclideProd.m."""

import numpy as np

from monalisa._mat import cell_items, iscell, mixed


def _prod(x1, x2, H):
    a = np.ravel(np.asarray(x1), order="F")
    b = np.ravel(np.asarray(x2), order="F")
    if np.size(H) == 1:
        Hb = mixed(np.multiply, np.asarray(H).reshape(()), b)
    else:
        Hb = mixed(np.multiply, np.ravel(np.asarray(H), order="F"), b)
    return np.real(np.vdot(a, Hb))


def euclidean_prod(x1, x2, H):
    """Weighted inner product ``real(x1' * (H .* x2))``, summed over cells."""
    if iscell(x1) and iscell(x2):
        Hs = cell_items(H) if iscell(H) else [H] * len(cell_items(x1))
        out = 0
        for a, b, h in zip(cell_items(x1), cell_items(x2), Hs, strict=True):
            out = out + _prod(a, b, h)
        return out
    if not iscell(x1) and not iscell(x2) and not iscell(H):
        return _prod(x1, x2, H)
    raise NotImplementedError("In euclidean_prod : case not implemented. ")
