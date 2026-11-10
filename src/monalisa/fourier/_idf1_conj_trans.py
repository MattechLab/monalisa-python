"""Port of src/fourier1/bmIDF1_conjTrans.m."""

import numpy as np
import scipy.fft

from monalisa._fft import fftshift, ifftshift
from monalisa._mat import msize, reshape, vec
from monalisa.array._block_reshape import block_reshape


def idf1_conj_trans(x, N_u, dK_u):
    """Adjoint of idf1 (centered FFT and scaling)."""
    argSize = msize(x)
    x = block_reshape(x, N_u)
    for n in range(1):
        x = fftshift(scipy.fft.fft(ifftshift(x, axes=n), axis=n, workers=-1, overwrite_x=True), axes=n)
    F = np.float32(np.prod(vec(dK_u)))
    x = x * F
    return reshape(x, argSize)
