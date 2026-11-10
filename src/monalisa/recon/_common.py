"""Shared helpers of the iterative solvers (MATLAB single-precision semantics)."""

import numpy as np


def dot(a, b):
    """MATLAB ``a(:)' * b(:)`` (single precision for single inputs)."""
    return np.vdot(np.ravel(a, order="F"), np.ravel(b, order="F"))


def sq(a, w):
    """``real(a(:)' * (w .* a(:)))`` with ``w`` scalar or array."""
    w = np.asarray(w)
    wa = (w * np.asarray(a)) if w.ndim == 0 else np.reshape(w, np.shape(a), order="F") * a
    return np.real(dot(a, wa))


def inv_single(h):
    """MATLAB ``1/h`` for single ``h``: double division rounded to single."""
    return np.float32(1.0 / np.float64(h))


def regul_param(p, nIter):
    """Constant or linearly varying single-precision parameter over the iterations."""
    p = np.abs(np.ravel(np.asarray(p, dtype=np.float32)))
    if p.size == 1:
        return np.full((1, int(nIter)), p[0], dtype=np.float32)
    return np.linspace(p[0], p[1], int(nIter), dtype=np.float32)[None, :]
