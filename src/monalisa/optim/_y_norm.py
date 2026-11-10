"""Port of src/linSpace/bmY_norm.m."""

import numpy as np

from monalisa._mat import isempty, mixed, msize, ndims
from monalisa.optim._y_ve_reshape import y_ve_reshape


def y_norm(y, d_n, collapse_flag=None):
    """Norm of each channel of ``y`` weighted by the volume elements ``d_n``;
    with ``collapse_flag`` the norm over all channels."""
    if isempty(collapse_flag):
        collapse_flag = False
    y = np.asarray(y)
    if ndims(y) > 2:
        raise ValueError("This function is for 2Dim arrays only. ")
    d_n = y_ve_reshape(d_n, msize(y))
    yd = mixed(np.multiply, y, d_n)
    axis = 0 if msize(y, 1) > msize(y, 2) else 1
    n = np.sqrt(np.abs(np.sum(np.conj(y) * yd, axis=axis, keepdims=True)))
    if collapse_flag:
        n = np.sqrt(np.sum(np.ravel(n, order="F") ** 2))
    return n
