"""Port of src/fourier123/map_function/nonCartesian/bmShanna_MATLAB.m."""

import numpy as np
import scipy.fft

from monalisa._mat import double, int32, isempty, msize, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.image123.bmImZeroFill import bmImZeroFill
from monalisa.sparseMat.m.bmSparseMat_vec import bmSparseMat_vec


def bmShanna_MATLAB(x, G, KFC, n_u):
    """Forward model: image ``x`` (column format) -> non-Cartesian data ``[nPt, nCh]``.

    ``x .* KFC``, zero filling to ``G.N_u``, centered FFT, interpolation ``G``.
    """
    if isempty(n_u):
        n_u = G.N_u
    N_u = double(int32(vec(G.N_u)))
    n_u = double(int32(vec(n_u)))
    imDim = N_u.size
    x = np.asarray(x)
    x_size_2 = msize(x, 2)
    nCh = msize(KFC, 2) if x_size_2 == 1 else x_size_2
    _check(x, G, KFC, N_u, n_u, nCh)
    if x_size_2 < nCh:
        x = np.tile(x, (1, nCh))
    x = x * KFC
    if not np.array_equal(N_u, n_u):
        x = bmBlockReshape(x, n_u)
        x = bmImZeroFill(x, N_u, n_u, "complex_single")
        x = bmColReshape(x, N_u)
    x = bmBlockReshape(x, N_u)
    for n in range(min(imDim, 3)):
        x = scipy.fft.fftshift(scipy.fft.fft(scipy.fft.ifftshift(x, axes=n), axis=n, workers=-1), axes=n)
    x = bmColReshape(x, N_u)
    return bmSparseMat_vec(G, x, "omp", "complex", False)


def _check(x, G, KFC, N_u, n_u, nCh):
    if x.dtype not in (np.float32, np.complex64):
        raise TypeError("The data'x' must be of class single")
    if np.asarray(KFC).dtype not in (np.float32, np.complex64):
        raise TypeError("The matrix 'K' must be of class single")
    if msize(x, 1) != np.prod(n_u):
        raise ValueError("The data matrix 'x' is not in the correct size")
    if msize(KFC) != (int(np.prod(n_u)), nCh):
        raise ValueError("The matrix 'K' is probably not in the correct size")
    if np.sum(np.mod(N_u, 2)) > 0 or np.sum(np.mod(n_u, 2)) > 0:
        raise ValueError("N_u and n_u must have all components even for the Fourier transform. ")
    if G.block_type != "one_block":
        raise ValueError("The block type of G must be 'one_block'. ")
    if G.type not in ("cpp_prepared", "l_squeezed_cpp_prepared"):
        raise ValueError("G is bmSparseMat but is not cpp_prepared. ")
