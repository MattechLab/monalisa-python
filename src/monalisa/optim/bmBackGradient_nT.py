"""Port of src/optim/bmBackGradient_nT.m."""

import numpy as np

from monalisa._mat import mixed, vec


def bmBackGradient_nT(x, n_u, dX_u, n):
    """Adjoint of ``bmBackGradient_n``."""
    n_u = vec(n_u).astype(np.int64)
    dX_u = vec(dX_u)
    shape = tuple(n_u) if n_u.size > 1 else (int(n_u[0]), 1)
    x = np.reshape(np.asarray(x), shape, order="F")
    ax = int(n) - 1
    g = x.copy()
    idx = [slice(None)] * g.ndim
    idx[ax] = 0
    g[tuple(idx)] = 0
    g = mixed(np.divide, g - np.roll(x, -1, axis=ax), dX_u[ax])
    return np.reshape(g, (-1, 1), order="F")
