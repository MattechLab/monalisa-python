"""Port of src/mathOp/bmAxpy.m."""

import numpy as np

from monalisa._mat import cell_from_items, cell_items, cell_shape, iscell, mixed


def _axpy(a, x, y):
    return mixed(np.add, mixed(np.multiply, a, x), y)


def bmAxpy(a, x, y):
    """``a .* x + y``, also for cells (``a`` scalar, array or cell)."""
    if iscell(a) and iscell(x) and iscell(y):
        items = [_axpy(ai, xi, yi) for ai, xi, yi in zip(cell_items(a), cell_items(x), cell_items(y), strict=True)]
        return cell_from_items(items, cell_shape(x))
    if not iscell(a) and iscell(x) and iscell(y):
        return cell_from_items([_axpy(a, xi, yi) for xi, yi in zip(cell_items(x), cell_items(y), strict=True)],
                               cell_shape(x))
    if not iscell(a) and not iscell(x) and not iscell(y):
        return _axpy(a, x, y)
    raise NotImplementedError("In bmAxpy: case not implemented. ")
