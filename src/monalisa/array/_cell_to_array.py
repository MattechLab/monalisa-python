"""Port of src/arrayUtility/bmCell2Array.m."""

import numpy as np

from monalisa._mat import cell_items, cell_shape, msize, reshape


def cell_to_array(c):
    """Stack the equally sized arrays of a cell into one array ``[size(c{1}), size(c)]``."""
    items = [np.asarray(a) for a in cell_items(c)]
    in_size = msize(items[0])
    a = np.zeros((int(np.prod(in_size)), len(items)), dtype=items[0].dtype, order="F")
    for i, x in enumerate(items):
        a[:, i] = np.ravel(x, order="F")
    return reshape(a, [*in_size, *cell_shape(c)])
