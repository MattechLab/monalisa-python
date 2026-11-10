"""Port of src/optim/bmBackGradient.m."""

import numpy as np

from monalisa._mat import vec
from monalisa.optim._back_gradient_n import back_gradient_n


def back_gradient(x, n_u, dX_u):
    """Backward-difference gradient ``[prod(n_u), imDim]`` (complex single)."""
    n_u = vec(n_u)
    g = np.zeros((int(np.prod(n_u)), n_u.size), dtype=np.complex64, order="F")
    for n in range(n_u.size):
        g[:, n] = back_gradient_n(x, n_u, dX_u, n + 1)[:, 0]
    return g
