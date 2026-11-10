"""Numba port of the bmSparseMat_*_mex matrix-vector products.

All MEX variants (real/complex, column/row vectors, one/multi block, with or
without OpenMP) compute, for each row, the sum of ``m_val * v`` over the row's
non-zeros in storage order, in float32. One kernel parallel over rows
reproduces them exactly.

Two loop orders give the same sums: vector by vector (``*_by_column``, fastest for arrays in
column order: each vector is contiguous) and all vectors of a row together (fastest when the
vectors of a row are contiguous). ``matvec`` picks the one that suits the layout.
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



@numba.njit(parallel=True, cache=True)
def csr_matvec_by_column(row_of, row_start, cols, vals, V, W, nb):
    """:func:`csr_matvec` for vectors in column order: each thread takes a block of rows and
    runs through the vectors one at a time (contiguous reads of ``V[:, k]`` around the row).
    ``nb``: number of blocks, one per thread (an argument, so that the kernel can be cached)."""
    n = row_of.size
    for b in numba.prange(nb):
        for k in range(V.shape[1]):
            for i in range(b * n // nb, (b + 1) * n // nb):
                acc = np.float32(0.0)
                for p in range(row_start[i], row_start[i + 1]):
                    acc += vals[p] * V[cols[p], k]
                W[row_of[i], k] = acc


@numba.njit(parallel=True, cache=True)
def csr_matvec_complex_by_column(row_of, row_start, cols, vals, V, W, nb):
    """:func:`csr_matvec_complex` for vectors in column order (see :func:`csr_matvec_by_column`)."""
    n = row_of.size
    for b in numba.prange(nb):
        for k in range(V.shape[1]):
            for i in range(b * n // nb, (b + 1) * n // nb):
                acc_r = np.float32(0.0)
                acc_i = np.float32(0.0)
                for p in range(row_start[i], row_start[i + 1]):
                    v = V[cols[p], k]
                    acc_r += vals[p] * v.real
                    acc_i += vals[p] * v.imag
                W[row_of[i], k] = complex(acc_r, acc_i)


def matvec(row_of, row_start, cols, vals, V, W):
    """``W = G V`` with the loop order suited to the memory layout of ``V`` and ``W``."""
    by_column = V.shape[1] > 1 and V.flags.f_contiguous and W.flags.f_contiguous
    if by_column:
        kernel = csr_matvec_complex_by_column if np.iscomplexobj(V) else csr_matvec_by_column
        kernel(row_of, row_start, cols, vals, V, W, numba.get_num_threads())
    else:
        kernel = csr_matvec_complex if np.iscomplexobj(V) else csr_matvec
        kernel(row_of, row_start, cols, vals, V, W)


def zeros(shape, dtype):
    """``np.zeros(shape, dtype, order="F")``, with the memory touched by all threads.

    Large NumPy arrays get huge pages, mapped (and cleared) on their first write: when the
    threads of a kernel write the columns of a fresh array together, they wait on the same few
    page faults. Clearing the array first in contiguous blocks, one per thread, maps it in
    parallel."""
    W = np.empty(shape, dtype, order="F")
    _clear(np.reshape(W, -1, order="F"), numba.get_num_threads())
    return W


@numba.njit(parallel=True, cache=True)
def _clear(flat, nb):
    n = flat.size
    for b in numba.prange(nb):
        for i in range(b * n // nb, (b + 1) * n // nb):
            flat[i] = 0
