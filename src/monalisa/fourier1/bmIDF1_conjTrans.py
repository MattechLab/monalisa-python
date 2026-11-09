"""Port of src/fourier1/bmIDF1_conjTrans.m."""

import numpy as np
import scipy.fft

from monalisa._fft import fftshift, ifftshift
from monalisa._mat import msize, reshape, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape


def bmIDF1_conjTrans(x, N_u, dK_u):
    """Adjoint of bmIDF1 (centered FFT and scaling)."""
    argSize = msize(x)
    x = bmBlockReshape(x, N_u)
    for n in range(1):
        x = fftshift(scipy.fft.fft(ifftshift(x, axes=n), axis=n, workers=-1, overwrite_x=True), axes=n)
    F = np.float32(np.prod(vec(dK_u)))
    x = x * F
    return reshape(x, argSize)
