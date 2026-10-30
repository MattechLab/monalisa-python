"""Port of src/mathOp/bmMult.m."""

import numpy as np

from monalisa._mat import cell_from_items, cell_items, cell_shape, iscell, mixed


def bmMult(x, y):
    """``x .* y`` element-wise, also for cells of arrays."""
    if iscell(x) and iscell(y):
        pairs = zip(cell_items(x), cell_items(y), strict=True)
        return cell_from_items([mixed(np.multiply, a, b) for a, b in pairs], cell_shape(x))
    if not iscell(x) and iscell(y):
        return cell_from_items([mixed(np.multiply, x, b) for b in cell_items(y)], cell_shape(y))
    if not iscell(x) and not iscell(y):
        return mixed(np.multiply, x, y)
    return None
