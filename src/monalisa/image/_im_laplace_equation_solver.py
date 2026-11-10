"""Port of src/image123/bmImLaplaceEquationSolver.m."""

import numpy as np

from monalisa.image._im_laplace_iterator import im_laplace_iterator
from monalisa.image._im_laplacian import im_laplacian


def im_laplace_equation_solver(imStart, m, nIter, L_th, omp_flag=None, nBlockPerThread=None):
    """Harmonic extension of ``imStart`` outside the mask ``m``: blocks of
    ``nIter`` iterations until the relative Laplacian norm outside ``m`` is
    below ``L_th``."""
    m_neg = ~np.ravel(np.asarray(m, dtype=bool), order="F")
    out = imStart
    while True:
        out = im_laplace_iterator(out, m, nIter, omp_flag, nBlockPerThread)
        L = im_laplacian(out)
        L_squared_norm = np.sum(np.abs(np.ravel(L, order="F")[m_neg]) ** 2)
        im_squared_norm = np.sum(np.abs(np.ravel(out, order="F")[m_neg]) ** 2)
        r = np.sqrt(L_squared_norm / im_squared_norm)
        if not r > L_th:
            return out
