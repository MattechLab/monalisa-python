"""Kernels for arrays in column order give the same values as the reference implementations."""

import numpy as np
import pytest
import scipy.fft
import scipy.sparse

from monalisa._fft import fftshift, ifftshift
from monalisa.sparse._sparse_vec import csr_matvec, csr_matvec_complex, matvec, zeros


@pytest.mark.parametrize("shape", [(6,), (5, 1), (6, 7), (5, 4, 3), (4, 6, 8, 3), (3, 5, 7, 2, 2)])
def test_shifts_match_scipy(shape):
    rng = np.random.default_rng(0)
    x = np.asfortranarray((rng.standard_normal(shape) + 1j * rng.standard_normal(shape)).astype(np.complex64))
    for axes in [(0,), (1,), (2,), (0, 1), (0, 2), (0, 1, 2), (3,)]:
        if max(axes) >= x.ndim:
            continue
        for ours, ref in ((fftshift, scipy.fft.fftshift), (ifftshift, scipy.fft.ifftshift)):
            got = ours(x, axes)
            np.testing.assert_array_equal(got, ref(x, axes=axes))
            assert got.shape == x.shape
    c = np.ascontiguousarray(x)  # other layouts: scipy's version
    np.testing.assert_array_equal(fftshift(c, 0), scipy.fft.fftshift(c, axes=0))


@pytest.mark.parametrize("cplx", [False, True])
def test_sparse_product_by_column_is_identical(cplx):
    rng = np.random.default_rng(1)
    A = scipy.sparse.random(3000, 2000, density=0.01, format="csr", random_state=rng, dtype=np.float32)
    rows = np.flatnonzero(np.diff(A.indptr))  # stored rows; the others stay zero
    row_start = np.concatenate([[0], np.cumsum(np.diff(A.indptr)[rows])]).astype(np.int64)
    cols = np.concatenate([A.indices[A.indptr[r]:A.indptr[r + 1]] for r in rows]).astype(np.int64)
    vals = np.concatenate([A.data[A.indptr[r]:A.indptr[r + 1]] for r in rows])
    V = rng.standard_normal((2000, 7)).astype(np.float32)
    if cplx:
        V = (V + 1j * rng.standard_normal((2000, 7))).astype(np.complex64)
    dtype = V.dtype
    ref = np.zeros((3000, 7), dtype)
    (csr_matvec_complex if cplx else csr_matvec)(rows.astype(np.int64), row_start, cols, vals, V, ref)
    W = zeros((3000, 7), dtype)
    assert W.flags.f_contiguous and not W.any()
    matvec(rows.astype(np.int64), row_start, cols, vals, np.asfortranarray(V), W)  # column-order kernel
    np.testing.assert_array_equal(W, ref)
