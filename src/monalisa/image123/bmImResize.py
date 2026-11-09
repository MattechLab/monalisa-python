"""Port of src/image123/bmImResize.m."""

import numpy as np

from monalisa._mat import numel, reshape, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.arrayUtility.bmIsColShape import bmIsColShape


def _keys_matrix(grid, query):
    """Interpolation matrix of MATLAB's uniform-grid 'cubic' method (Keys cubic
    convolution, a = -0.5, with Keys' boundary extrapolation
    f(-1) = 3 f(0) - 3 f(1) + f(2) and its mirror at the upper end)."""
    n = grid.size
    h = (grid[-1] - grid[0]) / (n - 1)
    s = (query - grid[0]) / h
    k = np.clip(np.floor(s).astype(np.int64), 0, n - 2)
    u = s - k
    # Keys weights for the samples k-1, k, k+1, k+2
    w = np.stack(
        [
            ((-0.5 * u + 1.0) * u - 0.5) * u,
            (1.5 * u - 2.5) * u * u + 1.0,
            ((-1.5 * u + 2.0) * u + 0.5) * u,
            (0.5 * u - 0.5) * u * u,
        ],
        axis=1,
    )
    W = np.zeros((query.size, n))
    rows = np.arange(query.size)
    for j, off in enumerate((-1, 0, 1, 2)):
        idx = k + off
        lo = idx < 0
        hi = idx > n - 1
        ok = ~(lo | hi)
        np.add.at(W, (rows[ok], idx[ok]), w[ok, j])
        # f(-1) = 3 f(0) - 3 f(1) + f(2)
        for col, c in ((0, 3.0), (1, -3.0), (2, 1.0)):
            np.add.at(W, (rows[lo], np.full(lo.sum(), col)), c * w[lo, j])
        # f(n) = 3 f(n-1) - 3 f(n-2) + f(n-3)
        for col, c in ((n - 1, 3.0), (n - 2, -3.0), (n - 3, 1.0)):
            np.add.at(W, (rows[hi], np.full(hi.sum(), col)), c * w[hi, j])
    return W


def bmImResize(argIm, n_u, N_u, interp_option=None):
    """Resample images of size ``n_u`` to size ``N_u`` on the periodic grid
    used by Monalisa (cubic interpolation by default). Returns double."""
    if interp_option is None:
        interp_option = "cubic"
    if interp_option != "cubic":
        raise NotImplementedError(f"bmImResize: interp_option {interp_option!r} not ported yet")
    N_u = vec(N_u)
    n_u = vec(n_u)
    imDim = n_u.size
    if imDim != N_u.size:
        raise ValueError("n_u and N_u must correspond to the same image dimension. ")
    nCh = numel(argIm) / np.prod(n_u)
    nCh_i = int(nCh)
    myIm = np.reshape(np.asarray(argIm), [*map(int, n_u), nCh_i], order="F")
    is_single = myIm.dtype in (np.float32, np.complex64)

    # periodic extension by one sample along each image axis
    for ax in range(imDim):
        myIm = np.concatenate([myIm, np.take(myIm, [0], axis=ax)], axis=ax)

    out = myIm
    for ax in range(imDim):
        grid = np.linspace(0, 1, int(n_u[ax]) + 1)
        query = np.mod(0.5 + np.arange(-N_u[ax] / 2, N_u[ax] / 2) / N_u[ax], 1)
        W = _keys_matrix(grid, query)
        if is_single:
            W = W.astype(np.float32)
        out = np.moveaxis(np.tensordot(W, out, axes=([1], [ax])), 0, ax)
    out = out.astype(np.complex128 if np.iscomplexobj(out) else np.float64, order="F")  # column order

    out = reshape(out, [*N_u, nCh])
    if bmIsColShape(argIm, N_u):
        return bmColReshape(out, N_u)
    return bmBlockReshape(out, N_u)
