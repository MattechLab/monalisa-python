"""Numba port of the bmSparseMat_*_mex matrix-vector products.

All MEX variants (real/complex, column/row vectors, one/multi block, with or
without OpenMP) compute, for each row, the sum of ``m_val * v`` over the row's
non-zeros in storage order, in float32. One kernel parallel over rows
reproduces them exactly.
"""

import numba
import numpy as np


@numba.njit(parallel=True, cache=True)
def csr_matvec(row_of, row_start, cols, vals, V, W):
    """``W[row_of[i], k] = sum_p vals[p] * V[cols[p], k]`` for the rows ``i``.

    ``V`` is ``(r_size, n_vec)`` float32, ``W`` is ``(l_size, n_vec)`` float32
    and zero-initialized (rows absent from ``row_of`` stay zero).
    """
    n_vec = V.shape[1]
    for i in numba.prange(row_of.size):
        r = row_of[i]
        for k in range(n_vec):
            acc = np.float32(0.0)
            for p in range(row_start[i], row_start[i + 1]):
                acc += vals[p] * V[cols[p], k]
            W[r, k] = acc


@numba.njit(parallel=True, cache=True)
def csr_matvec_complex(row_of, row_start, cols, vals, V, W):
    """Complex version of :func:`csr_matvec`: ``V`` complex64 (any memory layout), ``W``
    complex64. Real and imaginary parts are accumulated separately in float32, in the same
    order as two calls of :func:`csr_matvec` on ``real(V)`` and ``imag(V)``, so the result is
    identical, without copying the real and imaginary parts."""
    n_vec = V.shape[1]
    for i in numba.prange(row_of.size):
        r = row_of[i]
        for k in range(n_vec):
            acc_r = np.float32(0.0)
            acc_i = np.float32(0.0)
            for p in range(row_start[i], row_start[i + 1]):
                v = V[cols[p], k]
                acc_r += vals[p] * v.real
                acc_i += vals[p] * v.imag
            W[r, k] = complex(acc_r, acc_i)
