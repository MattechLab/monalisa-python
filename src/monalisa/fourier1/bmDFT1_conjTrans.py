"""Port of src/fourier1/bmDFT1_conjTrans.m."""

import numpy as np
import scipy.fft

from monalisa._fft import fftshift, ifftshift
from monalisa._mat import msize, reshape, single, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape


def bmDFT1_conjTrans(x, N_u, dK_u):
    """Adjoint of bmDFT1 (centered inverse FFT and scaling)."""
    argSize = msize(x)
    x = bmBlockReshape(x, N_u)
    for n in range(1):
        x = fftshift(scipy.fft.ifft(ifftshift(x, axes=n), axis=n, workers=-1, overwrite_x=True), axes=n)
    p = np.prod(single(vec(dK_u)))
    F_conj = np.float32(1.0 / np.float64(p))
    x = x * F_conj
    return reshape(x, argSize)
