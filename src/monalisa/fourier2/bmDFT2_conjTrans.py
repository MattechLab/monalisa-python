"""Port of src/fourier2/bmDFT2_conjTrans.m."""

import numpy as np
import scipy.fft

from monalisa._mat import msize, reshape, single, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape


def bmDFT2_conjTrans(x, N_u, dK_u):
    """Adjoint of bmDFT2 (centered inverse FFT and scaling)."""
    argSize = msize(x)
    x = bmBlockReshape(x, N_u)
    for n in range(2):
        x = scipy.fft.fftshift(scipy.fft.ifft(scipy.fft.ifftshift(x, axes=n), axis=n, workers=-1), axes=n)
    p = np.prod(single(vec(dK_u)))
    F_conj = np.float32(1.0 / np.float64(p))
    x = x * F_conj
    return reshape(x, argSize)
