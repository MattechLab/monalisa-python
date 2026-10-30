"""Port of src/image123/bmImZeroFill.m."""

import numpy as np

from monalisa._mat import msize, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmZero import bmZero


def bmImZeroFill(arg_im, N_u, n_u, argType):
    """Embed images of size ``n_u`` at the center of zero images of size ``N_u``."""
    N_u = vec(N_u)
    n_u = vec(n_u)
    imDim = N_u.size
    if imDim == 1:
        # upstream bug kept: the 1D branch reads an undefined variable 'u'
        raise NameError("Unrecognized function or variable 'u'.")
    arg_im = bmBlockReshape(arg_im, n_u)
    arg_im_size = msize(arg_im)
    if len(arg_im_size) == n_u.size and np.array_equal(arg_im_size, n_u):
        nCh = 1
    else:
        nCh = arg_im_size[-1]
    out_im = bmZero([*N_u, nCh], argType)
    out_im = np.reshape(out_im, [*map(int, N_u), nCh], order="F")
    sl = tuple(slice(int(N / 2 - n / 2), int(N / 2 + n / 2)) for N, n in zip(N_u, n_u, strict=True))
    out_im[sl] = np.reshape(arg_im, [*map(int, n_u), nCh], order="F")
    return bmBlockReshape(out_im, N_u) if nCh == 1 else out_im
