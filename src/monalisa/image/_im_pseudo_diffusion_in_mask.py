"""Port of src/image123/bmImPseudoDiffusion_inMask.m."""

import numpy as np

from monalisa._mat import imsize_ints as _ims
from monalisa._mat import isempty, msize, single, squeeze
from monalisa.image._im_reshape import im_reshape

_SHIFTS = {
    1: [(0,), (1,), (-1,)],
    2: [(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0)],
    3: [(0, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0)],
}


def im_pseudo_diffusion_in_mask(argIm, argMask, nIter=None):
    """Smoothing restricted to the mask (averages of the masked cross neighbours);
    values outside the mask are kept."""
    if isempty(nIter):
        nIter = 1
    argIm = np.asarray(argIm)
    myIm, imDim, imSize = _ims(im_reshape(single(squeeze(argIm)), nargout=3))
    myIm = np.array(myIm)
    myMask = np.reshape(np.asarray(argMask, dtype=bool), imSize, order="F")
    myMask_neg = ~myMask
    shifts = _SHIFTS[imDim]
    for _ in range(int(nIter)):
        myIm[myMask_neg] = 0
        temp_im = np.zeros(imSize, dtype=myIm.dtype)
        myNumOfNeighb = np.zeros(imSize, dtype=np.float32)
        for sh in shifts:
            ax = tuple(range(imDim))
            temp_im = temp_im + np.roll(myIm, sh, axis=ax)
            myNumOfNeighb = myNumOfNeighb + np.roll(myMask, sh, axis=ax).astype(np.float32)
        myNumOfNeighb[myNumOfNeighb == 0] = 1
        myIm = temp_im / myNumOfNeighb
    myIm = np.reshape(myIm, msize(argIm), order="F")
    myMask_neg = np.reshape(myMask_neg, msize(argIm), order="F")
    myIm[myMask_neg] = argIm[myMask_neg]
    return myIm
