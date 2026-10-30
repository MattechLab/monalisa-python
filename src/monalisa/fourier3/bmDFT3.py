"""Port of src/fourier3/bmDFT3.m."""

import numpy as np
import scipy.fft

from monalisa._mat import mixed, msize, reshape
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape


def bmDFT3(x, N_u, dK_u):
    """Centered 3D Fourier transform scaled by 1/(prod(N_u)*prod(dK_u))."""
    argSize = msize(x)
    x = bmBlockReshape(x, N_u)
    for n in range(3):
        x = scipy.fft.fftshift(scipy.fft.fft(scipy.fft.ifftshift(x, axes=n), axis=n, workers=-1), axes=n)
    F = np.prod(np.ravel(N_u)) * np.prod(np.ravel(dK_u))
    x = mixed(np.divide, x, F)
    return reshape(x, argSize)
