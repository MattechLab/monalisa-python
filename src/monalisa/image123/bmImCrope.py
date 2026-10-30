"""Port of src/image123/bmImCrope.m."""

import numpy as np

from monalisa._mat import vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape


def bmImCrope(arg_im, N_u, n_u):
    """Crop the centered region of size ``n_u`` from images of size ``N_u``."""
    N_u = vec(N_u)
    n_u = vec(n_u)
    if np.array_equal(N_u, n_u):
        return arg_im
    im = bmBlockReshape(arg_im, N_u)
    sl = tuple(slice(int(N / 2 - n / 2), int(N / 2 + n / 2)) for N, n in zip(N_u, n_u, strict=True))
    return im[sl + (slice(None),) * (im.ndim - len(sl))]
