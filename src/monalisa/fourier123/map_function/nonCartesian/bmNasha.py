"""Port of src/fourier123/map_function/nonCartesian/bmNasha.m."""

import numpy as np

from monalisa._mat import double, int32, isempty, msize, single, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.coilSense.map.bmCoilSense_pinv import bmCoilSense_pinv
from monalisa.fourier1.bmIDF1 import bmIDF1
from monalisa.fourier2.bmIDF2 import bmIDF2
from monalisa.fourier3.bmIDF3 import bmIDF3
from monalisa.fourier123.prep_function.bmK import bmK
from monalisa.image123.bmImCrope import bmImCrope
from monalisa.sparseMat.m.bmSparseMat_vec import bmSparseMat_vec


def bmNasha(y, G, n_u, C=None, K=None, fft_lib_flag=None):
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
        K = bmK(N_u, dK_u, nCh, G.kernel_type, G.nWin, G.kernelParam)
    K = single(bmBlockReshape(K, N_u))
    if isempty(fft_lib_flag):
        fft_lib_flag = "MATLAB"
    if fft_lib_flag != "MATLAB":
        raise NotImplementedError(f"bmNasha: fft_lib_flag {fft_lib_flag!r} is not available in Python")
    if not isempty(C):
        C = single(bmColReshape(C, n_u))
    else:
        C = None
    _check(y, G, K, C, N_u, n_u, nCh, nPt)

    x = bmSparseMat_vec(G, y, "omp", "complex")
    x = bmBlockReshape(x, N_u)
    x = {1: bmIDF1, 2: bmIDF2, 3: bmIDF3}[imDim](x, N_u, dK_u)
    x = x * K
    if not np.array_equal(N_u, n_u):
        x = bmImCrope(x, N_u, n_u)
    if C is not None:
        x = bmCoilSense_pinv(C, x, n_u)
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
