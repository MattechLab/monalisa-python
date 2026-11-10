"""Port of src/arrayUtility/bmZero.m."""

import numpy as np

from monalisa._mat import cell_from_items, isempty, vec

_TYPES = {
    "real_double": np.float64,
    "complex_double": np.complex128,
    "real_single": np.float32,
    "complex_single": np.complex64,
}


def zero(argSize, argType, frame_size=None):
    """Zero array of size ``argSize`` and type ``'real_double'``, ``'complex_double'``,
    ``'real_single'`` or ``'complex_single'``; a cell of them if ``frame_size`` is given."""
    if not isempty(frame_size):
        shape = [int(s) for s in vec(frame_size)]
        if len(shape) == 1:
            shape = [shape[0], shape[0]]
        n = int(np.prod(shape))
        return cell_from_items([zero(argSize, argType) for _ in range(n)], shape)
    if argType not in _TYPES:
        return None
    dims = [int(s) for s in vec(argSize)]
    if len(dims) == 1:
        dims = [dims[0], dims[0]]
    while len(dims) > 2 and dims[-1] == 1:
        dims.pop()
    return np.zeros(dims, dtype=_TYPES[argType], order="F")
