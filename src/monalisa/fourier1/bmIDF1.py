"""Port of src/fourier1/bmIDF1.m."""

import numpy as np
import scipy.fft

from monalisa._mat import mixed, msize, reshape
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape


def bmIDF1(x, N_u, dK_u):
    """Centered 1D inverse Fourier transform scaled by prod(N_u)*prod(dK_u)."""
    argSize = msize(x)
    x = bmBlockReshape(x, N_u)
    for n in range(1):
        x = scipy.fft.fftshift(scipy.fft.ifft(scipy.fft.ifftshift(x, axes=n), axis=n, workers=-1), axes=n)
    F = np.prod(np.ravel(N_u)) * np.prod(np.ravel(dK_u))
    x = mixed(np.multiply, x, F)
    return reshape(x, argSize)
