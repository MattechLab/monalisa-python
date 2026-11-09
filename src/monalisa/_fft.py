"""``fftshift`` / ``ifftshift`` for arrays in column order, as a parallel copy.

Drop-in replacements for ``scipy.fft.fftshift`` / ``ifftshift``: the same values (a shift is a
permutation), computed by all threads when the array is in column order and the shifted axes
are among the first three (image axes); otherwise scipy's single-threaded version is used.
The result is always a new array, so an FFT can then transform it in place (``overwrite_x``),
which keeps it in column order.
"""

import numba
import numpy as np
import scipy.fft


def fftshift(x, axes):
    return _shift(x, axes, inverse=False)


def ifftshift(x, axes):
    return _shift(x, axes, inverse=True)


def _shift(x, axes, inverse):
    x = np.asarray(x)
    axes = (axes,) if np.isscalar(axes) else tuple(axes)
    if not axes or min(axes) < 0 or max(axes) > 2 or x.ndim <= max(axes) or not x.flags.f_contiguous:
        return (scipy.fft.ifftshift if inverse else scipy.fft.fftshift)(x, axes=axes)
    n = list(x.shape[:3]) + [1] * (3 - min(x.ndim, 3))
    x4 = np.reshape(x, (*n, -1), order="F")  # view: column order
    # out[i] = x[(i + s) % n]: ifftshift shifts by n // 2, fftshift by n - n // 2, other axes by 0
    s = [(m // 2 if inverse else m - m // 2) if d in axes else 0 for d, m in enumerate(n)]
    out = np.empty_like(x4)
    _shift4(x4, out, s[0], s[1], s[2])
    return np.reshape(out, x.shape, order="F")


@numba.njit(parallel=True, cache=True)
def _shift4(x, out, s0, s1, s2):
    """``out[i, j, k, c] = x[(i + s0) % n0, (j + s1) % n1, (k + s2) % n2, c]`` (column order)."""
    n0, n1, n2, nc = x.shape
    for q in numba.prange(n2 * nc):
        c = q // n2
        k = q - c * n2
        ks = (k + s2) % n2
        for j in range(n1):
            js = (j + s1) % n1
            for i in range(n0 - s0):
                out[i, j, k, c] = x[i + s0, js, ks, c]
            for i in range(n0 - s0, n0):
                out[i, j, k, c] = x[i + s0 - n0, js, ks, c]
