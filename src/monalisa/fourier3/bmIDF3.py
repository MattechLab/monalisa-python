"""Port of src/fourier3/bmIDF3.m."""

import numpy as np
import scipy.fft

from monalisa._fft import fftshift, ifftshift
from monalisa._mat import msize, reshape
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape


def bmIDF3(x, N_u, dK_u):
    """Centered 3D inverse Fourier transform scaled by prod(N_u)*prod(dK_u)."""
    argSize = msize(x)
    x = bmBlockReshape(x, N_u)
    for n in range(3):
        x = fftshift(scipy.fft.ifft(ifftshift(x, axes=n), axis=n, workers=-1, overwrite_x=True), axes=n)
    F = np.float32(np.prod(np.ravel(N_u)) * np.prod(np.ravel(dK_u)))
    x = x * F
    return reshape(x, argSize)
