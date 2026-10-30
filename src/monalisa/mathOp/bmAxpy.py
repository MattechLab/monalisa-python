"""Port of src/mathOp/bmAxpy.m."""

import numpy as np

from monalisa._mat import cell_from_items, cell_items, cell_shape, iscell


def bmAxpy(a, x, y):
    """``a .* x + y``, also for cells (``a`` scalar, array or cell)."""
    if iscell(a) and iscell(x) and iscell(y):
        items = [ai * xi + yi for ai, xi, yi in zip(cell_items(a), cell_items(x), cell_items(y), strict=True)]
        return cell_from_items(items, cell_shape(x))
    if not iscell(a) and iscell(x) and iscell(y):
        return cell_from_items([a * xi + yi for xi, yi in zip(cell_items(x), cell_items(y), strict=True)],
                               cell_shape(x))
    if not iscell(a) and not iscell(x) and not iscell(y):
        return np.asarray(a) * x + y if np.size(a) != 1 else a * x + y
    raise NotImplementedError("In bmAxpy: case not implemented. ")
