"""Port of src/optim/bmBackGradientT.m."""

import numpy as np

from monalisa._mat import vec
from monalisa.optim.bmBackGradient_nT import bmBackGradient_nT


def bmBackGradientT(g, n_u, dX_u):
    """Adjoint of ``bmBackGradient`` (complex single column)."""
    n_u = vec(n_u)
    g = np.asarray(g)
    x = np.zeros((int(np.prod(n_u)), 1), dtype=np.complex64)
    for n in range(n_u.size):
        x = x + bmBackGradient_nT(g[:, n], n_u, dX_u, n + 1)
    return x
