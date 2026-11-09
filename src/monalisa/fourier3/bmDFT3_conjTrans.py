"""Port of src/fourier3/bmDFT3_conjTrans.m."""

import numpy as np
import scipy.fft

from monalisa._fft import fftshift, ifftshift
from monalisa._mat import msize, reshape, single, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape


def bmDFT3_conjTrans(x, N_u, dK_u):
    """Adjoint of bmDFT3 (centered inverse FFT and scaling)."""
    argSize = msize(x)
    x = bmBlockReshape(x, N_u)
    for n in range(3):
        x = fftshift(scipy.fft.ifft(ifftshift(x, axes=n), axis=n, workers=-1, overwrite_x=True), axes=n)
    F_conj = np.prod(single(vec(dK_u)))
    x = x / F_conj
    return reshape(x, argSize)
