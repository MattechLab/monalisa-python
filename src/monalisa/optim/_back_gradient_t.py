"""Port of src/optim/bmBackGradientT.m."""

import numpy as np

from monalisa._mat import vec
from monalisa.optim._back_gradient_n_t import back_gradient_n_t


def back_gradient_t(g, n_u, dX_u):
    """Adjoint of ``back_gradient`` (complex single column)."""
    n_u = vec(n_u)
    g = np.asarray(g)
    x = np.zeros((int(np.prod(n_u)), 1), dtype=np.complex64)
    for n in range(n_u.size):
        x = x + back_gradient_n_t(g[:, n], n_u, dX_u, n + 1)
    return x
