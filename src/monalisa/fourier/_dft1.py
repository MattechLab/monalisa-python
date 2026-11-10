"""Port of src/fourier1/bmDFT1.m."""

import numpy as np
import scipy.fft

from monalisa._fft import fftshift, ifftshift
from monalisa._mat import mixed, msize, reshape
from monalisa.array._block_reshape import block_reshape


def dft1(x, N_u, dK_u):
    """Centered 1D Fourier transform scaled by 1/(prod(N_u)*prod(dK_u))."""
    argSize = msize(x)
    x = block_reshape(x, N_u)
    for n in range(1):
        x = fftshift(scipy.fft.fft(ifftshift(x, axes=n), axis=n, workers=-1, overwrite_x=True), axes=n)
    F = np.prod(np.ravel(N_u)) * np.prod(np.ravel(dK_u))
    x = mixed(np.divide, x, F)
    return reshape(x, argSize)
