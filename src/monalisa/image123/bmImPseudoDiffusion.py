"""Port of src/image123/bmImPseudoDiffusion.m."""

import numpy as np

from monalisa._mat import imsize_ints as _ims
from monalisa._mat import isempty, msize, single, squeeze
from monalisa.image123.bmImReshape import bmImReshape

_SHIFTS = {
    1: [(0,), (1,), (-1,)],
    2: [(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0)],
    3: [(0, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0)],
}


def bmImPseudoDiffusion(argIm, nIter=None):
    """Smoothing by repeated averaging over the cross neighbourhood (periodic), single precision."""
    if isempty(nIter):
        nIter = 1
    argIm = np.asarray(argIm)
    myIm, imDim, imSize = _ims(bmImReshape(single(squeeze(argIm)), nargout=3))
    myIm = np.array(myIm)

    shifts = _SHIFTS[imDim]
    for _ in range(int(nIter)):
        temp_im = np.zeros(imSize, dtype=myIm.dtype)
        for sh in shifts:
            temp_im = temp_im + np.roll(myIm, sh, axis=tuple(range(imDim)))
        myIm = temp_im / np.float32(imDim * 2 + 1)
    myIm = np.reshape(myIm, msize(argIm), order="F")

    return myIm
