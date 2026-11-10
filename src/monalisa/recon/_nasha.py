"""Port of src/fourier123/map_function/nonCartesian/bmNasha.m."""

import numpy as np

from monalisa._mat import double, int32, isempty, msize, single, vec
from monalisa.array._block_reshape import block_reshape
from monalisa.array._col_reshape import col_reshape
from monalisa.coil._coil_sense_pinv import coil_sense_pinv
from monalisa.fourier._deapodization import deapodization
from monalisa.fourier._idf1 import idf1
from monalisa.fourier._idf2 import idf2
from monalisa.fourier._idf3 import idf3
from monalisa.image._im_crop import im_crop
from monalisa.sparse._sparse_mat_vec import sparse_mat_vec


def nasha(y, G, n_u, C=None, K=None, fft_lib_flag=None):
    """Gridded reconstruction with a precomputed gridding matrix ``G`` (``Gn``).

    ``y`` is ``[nPt, nCh]`` single. Gridding, centered inverse FFT,
    deapodization ``K``, cropping to ``n_u`` and, with ``C``, coil combination.
    """
    if isempty(n_u):
        n_u = G.N_u
    y = np.asarray(y)
    if y.dtype not in (np.float32, np.complex64):
        y = single(y)
    N_u = double(int32(vec(G.N_u)))
    n_u = double(int32(vec(n_u)))
    dK_u = double(single(vec(G.d_u)))
    imDim = N_u.size
    nPt = int(G.r_size)
    nCh = msize(y, 2)
    if isempty(K):
        K = deapodization(N_u, dK_u, nCh, G.kernel_type, G.nWin, G.kernelParam)
    K = single(block_reshape(K, N_u))
    if isempty(fft_lib_flag):
        fft_lib_flag = "MATLAB"
    if fft_lib_flag != "MATLAB":
        raise NotImplementedError(f"nasha: fft_lib_flag {fft_lib_flag!r} is not available in Python")
    if not isempty(C):
        C = single(col_reshape(C, n_u))
    else:
        C = None
    _check(y, G, K, C, N_u, n_u, nCh, nPt)

    x = sparse_mat_vec(G, y, "omp", "complex")
    x = block_reshape(x, N_u)
    x = {1: idf1, 2: idf2, 3: idf3}[imDim](x, N_u, dK_u)
    x = x * K
    if not np.array_equal(N_u, n_u):
        x = im_crop(x, N_u, n_u)
    if C is not None:
        x = coil_sense_pinv(C, x, n_u)
    return x


def _check(y, G, K, C, N_u, n_u, nCh, nPt):
    if msize(y) != (nPt, nCh):
        raise ValueError("The data matrix 'y' is not in the correct size. ")
    if msize(K) not in (tuple(int(n) for n in N_u) + (nCh,), tuple(int(n) for n in N_u)):
        raise ValueError("The matrix 'K' is not in the correct size. ")
    if C is not None and msize(C) != (int(np.prod(n_u)), nCh):
        raise ValueError("The matrix 'C' has not the correct size. ")
    if np.sum(np.mod(N_u, 2)) > 0:
        raise ValueError("N_u must have all components even for the Fourier transform. ")
    if G.block_type != "one_block":
        raise ValueError("The block type of G must be 'one_block'. ")
    if G.type not in ("cpp_prepared", "l_squeezed_cpp_prepared"):
        raise ValueError("G is not cpp_prepared. ")
