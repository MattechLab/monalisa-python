"""Port of src/fourier2/bmDFT2_conjTrans.m."""

import numpy as np
import scipy.fft

from monalisa._fft import fftshift, ifftshift
from monalisa._mat import msize, reshape, single, vec
from monalisa.array._block_reshape import block_reshape


def dft2_conj_trans(x, N_u, dK_u):
    """Adjoint of dft2 (centered inverse FFT and scaling)."""
    argSize = msize(x)
    x = block_reshape(x, N_u)
    for n in range(2):
        x = fftshift(scipy.fft.ifft(ifftshift(x, axes=n), axis=n, workers=-1, overwrite_x=True), axes=n)
    p = np.prod(single(vec(dK_u)))
    F_conj = np.float32(1.0 / np.float64(p))
    x = x * F_conj
    return reshape(x, argSize)
