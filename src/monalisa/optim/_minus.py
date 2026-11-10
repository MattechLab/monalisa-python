"""Port of src/mathOp/bmMinus.m."""

import numpy as np

from monalisa._mat import cell_from_items, cell_items, cell_shape, iscell, mixed


def minus(x, y):
    """``x - y`` element-wise, also for cells of arrays."""
    if iscell(x) and iscell(y):
        pairs = zip(cell_items(x), cell_items(y), strict=True)
        return cell_from_items([mixed(np.subtract, a, b) for a, b in pairs], cell_shape(x))
    if not iscell(x) and not iscell(y):
        return mixed(np.subtract, x, y)
    if not iscell(x) and iscell(y):
        return cell_from_items([mixed(np.subtract, x, b) for b in cell_items(y)], cell_shape(y))
    raise NotImplementedError("In minus : case not implemented. ")
