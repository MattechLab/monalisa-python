"""Port of src/linSpace/bmProx_oneNorm.m."""

import numpy as np

from monalisa._mat import cell_from_items, cell_items, cell_shape, iscell, msize, single


def _soft(w, s):
    plus = (w > s).astype(np.float32)
    minus = (w < -s).astype(np.float32)
    return plus * (w - s) + minus * (w + s)


def bmProx_oneNorm(w, s):
    """Proximal operator of ``s * ||.||_1``: soft thresholding (real and imaginary
    parts separately for complex data), single precision."""
    if iscell(w):
        return cell_from_items([bmProx_oneNorm(a, s) for a in cell_items(w)], cell_shape(w))
    argSize = msize(w)
    w = single(np.ravel(np.asarray(w), order="F"))
    s = np.float32(np.abs(np.asarray(s)).item())
    if not np.iscomplexobj(w):
        z = _soft(w, s)
    else:
        z = (_soft(w.real, s) + 1j * _soft(w.imag, s)).astype(np.complex64)
    return np.reshape(z, argSize, order="F")
