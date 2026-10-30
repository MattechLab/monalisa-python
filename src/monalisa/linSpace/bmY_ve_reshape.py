"""Port of src/linSpace/bmY_ve_reshape.m."""

import numpy as np

from monalisa._mat import col, msize, vec


def bmY_ve_reshape(ve, y_size):
    """Expand volume elements ``ve`` to the size ``y_size`` of the data ``[nPt, nCh]``."""
    y_size = tuple(int(s) for s in vec(y_size))
    ve = np.asarray(ve)
    s1, s2 = msize(ve, 1), msize(ve, 2)
    if s1 == y_size[0] and s2 == y_size[1]:
        return ve
    nPt, nCh = y_size[0], y_size[1]
    if nPt == 1 and nCh == 1:
        raise ValueError("ve is not reshapable in the given size. ")
    rawFlag = False
    if nPt < nCh:
        rawFlag = True
        nPt, nCh = nCh, nPt
    if s1 == 1 and s2 == 1:
        ve_out = ve.reshape(1, 1) * np.ones((nPt, nCh))
        ve_out = ve_out.astype(np.result_type(ve.dtype, np.float32) if ve.dtype == np.float32 else np.float64)
    elif s1 > 1 and s2 == 1:
        ve_out = np.tile(np.reshape(ve, (-1, 1), order="F"), (1, nCh))
    elif s1 == 1 and s2 > 1:
        ve_out = np.tile(col(ve), (1, nCh))
    elif not (s1 == nPt) or not (s2 == nCh):
        ve_out = ve.T
    else:
        raise NameError("Unrecognized function or variable 've_out'.")
    if rawFlag:
        ve_out = ve_out.T
    if msize(ve_out) != y_size:
        raise ValueError("ve is not reshapable in the given size. ")
    return ve_out
