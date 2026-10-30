"""Port of src/optim/bmBackGradient_n.m."""

import numpy as np

from monalisa._mat import mixed, vec


def bmBackGradient_n(x, n_u, dX_u, n):
    """Backward finite difference along dimension ``n`` (1-based), zero on the first slice."""
    n_u = vec(n_u).astype(np.int64)
    dX_u = vec(dX_u)
    shape = tuple(n_u) if n_u.size > 1 else (int(n_u[0]), 1)
    x = np.reshape(np.asarray(x), shape, order="F")
    ax = int(n) - 1
    g = mixed(np.divide, x - np.roll(x, 1, axis=ax), dX_u[ax])
    idx = [slice(None)] * g.ndim
    idx[ax] = 0
    g[tuple(idx)] = 0
    return np.reshape(g, (-1, 1), order="F")
