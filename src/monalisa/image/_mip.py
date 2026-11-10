"""Port of src/imageN/bmMIP.m."""

import numpy as np

from monalisa._mat import squeeze
from monalisa.array._block_reshape import block_reshape
from monalisa.array._col_reshape import col_reshape
from monalisa.array._is_block_shape import is_block_shape
from monalisa.array._is_col_shape import is_col_shape


def mip(y, N_u):
    """Maximum intensity projection over the channels."""
    c = col_reshape(y, N_u)
    a = squeeze(np.max(np.abs(c), axis=1, keepdims=True))
    if is_col_shape(y, N_u):
        a = col_reshape(a, N_u)
    elif is_block_shape(y, N_u):
        a = block_reshape(a, N_u)
    return a
