"""Port of src/image123/bmImLaplaceIterator.m."""

import numpy as np

from monalisa._mat import imsize_ints as _ims
from monalisa._mat import msize
from monalisa.image._im_reshape import im_reshape
from monalisa.image._laplace import laplace_solve, offsets


def im_laplace_iterator(imStart, m, nIter, omp_flag=None, nBlockPerThread=None):
    """``nIter`` (rounded up to even) Jacobi iterations of the discrete Laplace
    equation, keeping the voxels where ``m`` is true at their initial value.
    Real and imaginary parts are solved separately, in single precision."""
    argSize = msize(imStart)
    imStart, imDim, imSize = _ims(im_reshape(imStart, nargout=3))
    shape = imSize if imDim > 1 else (imSize[0],)
    off = offsets(shape[:imDim])
    mflat = np.ravel(np.asarray(m, dtype=bool), order="F")

    def solve(part):
        flat = np.ascontiguousarray(np.ravel(np.asarray(part, dtype=np.float32), order="F"))
        return laplace_solve(flat, mflat, int(nIter), off)

    imStart = np.asarray(imStart)
    if np.iscomplexobj(imStart):
        out = (solve(imStart.real) + 1j * solve(imStart.imag)).astype(np.complex64)
    else:
        out = solve(imStart)
    return np.reshape(out, argSize, order="F")
