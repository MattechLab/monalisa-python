"""Port of src/optim/bmBackGradient.m."""

import numpy as np

from monalisa._mat import vec
from monalisa.optim.bmBackGradient_n import bmBackGradient_n


def bmBackGradient(x, n_u, dX_u):
    """Backward-difference gradient ``[prod(n_u), imDim]`` (complex single)."""
    n_u = vec(n_u)
    g = np.zeros((int(np.prod(n_u)), n_u.size), dtype=np.complex64, order="F")
    for n in range(n_u.size):
        g[:, n] = bmBackGradient_n(x, n_u, dX_u, n + 1)[:, 0]
    return g
