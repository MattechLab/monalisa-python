"""Numba ports of bmImCrossMean{1,2,3}, bmImLaplaceEquationSolver{1,2,3}(_omp)
and bmImLaplacian{1,2,3} MEX kernels.

The kernels address neighbours by linear offsets (+-1, +-sx, +-sx*sy) taken
modulo the number of voxels of the column-major array, exactly like the C++
code (so they wrap across rows and slices, not per axis). Results do not
depend on the OpenMP block partition.
"""

import numba
import numpy as np


def offsets(shape):
    """Linear neighbour offsets in the order of the C++ sums: x+, x-, y+, y-, z+, z-."""
    off = []
    stride = 1
    for s in shape:
        off += [stride, -stride]
        stride *= s
    return np.array(off, dtype=np.int64)


@numba.njit(parallel=True, cache=True)
def cross_mean(inp, out, off):
    N = inp.size
    # -Ofast compiles the C++ "/ 7" as a multiplication by the float reciprocal
    inv = np.float32(1.0) / np.float32(off.size + 1)
    for i in numba.prange(N):
        s = inp[i]
        for k in range(off.size):
            s += inp[(i + off[k]) % N]
        out[i] = s * inv


@numba.njit(cache=True)
def clamp(x, m, c):
    for i in range(x.size):
        if m[i]:
            x[i] = c[i]


@numba.njit(cache=True)
def laplace_solve(imStart, m, nIter, off):
    out = imStart.copy()
    out2 = imStart.copy()
    for _ in range(int(np.ceil(nIter / 2.0))):
        cross_mean(out, out2, off)
        clamp(out2, m, imStart)
        cross_mean(out2, out, off)
        clamp(out, m, imStart)
    return out


@numba.njit(parallel=True, cache=True)
def laplacian(inp, off):
    N = inp.size
    out = np.empty_like(inp)
    c = np.float32(off.size)
    for i in numba.prange(N):
        s = inp[(i + off[0]) % N]
        for k in range(1, off.size):
            s += inp[(i + off[k]) % N]
        out[i] = s - c * inp[i]
    return out
