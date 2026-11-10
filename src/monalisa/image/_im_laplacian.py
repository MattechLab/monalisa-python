"""Port of src/image123/bmImLaplacian.m."""

import numpy as np

from monalisa._mat import imsize_ints as _ims
from monalisa._mat import msize
from monalisa.image._im_reshape import im_reshape
from monalisa.image._laplace import laplacian, offsets


def im_laplacian(argIm):
    """Discrete Laplacian (linear-offset neighbours, see ``mex/_laplace``), single precision."""
    argSize = msize(argIm)
    argIm, imDim, imSize = _ims(im_reshape(argIm, nargout=3))
    off = offsets(imSize[:imDim] if imDim > 1 else (imSize[0],))

    def lap(part):
        return laplacian(np.ascontiguousarray(np.ravel(np.asarray(part, dtype=np.float32), order="F")), off)

    argIm = np.asarray(argIm)
    if np.iscomplexobj(argIm):
        out = (lap(argIm.real) + 1j * lap(argIm.imag)).astype(np.complex64)
    else:
        out = lap(argIm)
    return np.reshape(out, argSize, order="F")
