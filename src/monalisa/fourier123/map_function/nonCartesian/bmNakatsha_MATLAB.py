"""Port of src/fourier123/map_function/nonCartesian/bmNakatsha_MATLAB.m."""

import numpy as np
import scipy.fft

from monalisa._mat import double, int32, isempty, msize, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.fourier123.map_function.nonCartesian._centered_fft import centered_fft
from monalisa.image123.bmImCrope import bmImCrope
from monalisa.sparseMat.m.bmSparseMat_vec import bmSparseMat_vec


def bmNakatsha_MATLAB(y, G, KFC_conj, C_flag, n_u):
    """Adjoint model: data ``y`` ``[nPt, nCh]`` -> image (column format).

    Gridding ``G`` (normally ``Gut``), centered inverse FFT, cropping to
    ``n_u``, multiplication by ``KFC_conj`` and, if ``C_flag``, sum over coils.
    """
    if isempty(C_flag):
        C_flag = False
    if isempty(n_u):
        n_u = G.N_u
    N_u = double(int32(vec(G.N_u)))
    n_u = double(int32(vec(n_u)))
    nPt = int(G.r_size)
    imDim = N_u.size
    y = np.asarray(y)
    nCh = msize(y, 2)
    _check(y, G, KFC_conj, C_flag, N_u, n_u, nPt, nCh)
    x = bmSparseMat_vec(G, y, "omp", "complex", False)
    x = bmBlockReshape(x, N_u)
    x = centered_fft(x, min(imDim, 3), scipy.fft.ifft)
    x = bmColReshape(x, N_u)
    if not np.array_equal(N_u, n_u):
        x = bmBlockReshape(x, N_u)
        x = bmImCrope(x, N_u, n_u)
        x = bmColReshape(x, n_u)
    x = x * KFC_conj
    if C_flag:
        x = np.sum(x, axis=1, keepdims=True)
    return x


def _check(y, G, KFC_conj, C_flag, N_u, n_u, nPt, nCh):
    if y.dtype not in (np.float32, np.complex64):
        raise TypeError("The data 'y' must be of class single")
    if np.asarray(KFC_conj).dtype not in (np.float32, np.complex64):
        raise TypeError("The matrix 'KFC_conj' must be of class single")
    if msize(y) != (nPt, nCh):
        raise ValueError("The data matrix 'y' is not in the correct size")
    if C_flag and msize(KFC_conj) != (int(np.prod(n_u)), nCh):
        raise ValueError("The matrix 'KFC_conj' has not the correct size")
    if np.sum(np.mod(N_u, 2)) > 0 or np.sum(np.mod(n_u, 2)) > 0:
        raise ValueError("N_u and n_u must have all components even for the Fourier transform. ")
    if G.block_type != "one_block":
        raise ValueError("The block type of G must be 'one_block'. ")
    if G.type not in ("cpp_prepared", "l_squeezed_cpp_prepared"):
        raise ValueError("G is bmSparseMat but is not cpp_prepared. ")
