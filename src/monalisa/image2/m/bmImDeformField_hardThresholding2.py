"""Port of src/image2/m/bmImDeformField_hardThresholding2.m."""

import numpy as np

from monalisa._mat import msize, reshape
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape


def bmImDeformField_hardThresholding2(v, n_u, argTh):
    """Clip the length of the 2D displacement vectors of ``v`` to ``argTh`` pixels."""
    myEps = 1e-4
    argTh = float(np.asarray(argTh).item())
    if argTh <= myEps:
        raise ValueError("The input threshold is smaller than the chosen machine epsilon.It does not make sense. ")
    argSize = msize(v)
    v = bmBlockReshape(v, n_u)
    v_norm = np.sqrt(v[:, :, 0] ** 2 + v[:, :, 1] ** 2)
    m = np.repeat((v_norm > argTh)[:, :, None], 2, axis=2)
    v_norm = np.where(v_norm <= myEps, 1, v_norm).astype(v_norm.dtype)
    v_norm = np.repeat(v_norm[:, :, None], 2, axis=2)
    v_normalized = argTh * v / v_norm
    w = v * (~m) + v_normalized * m
    return reshape(w, argSize)
