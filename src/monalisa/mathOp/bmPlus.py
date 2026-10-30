"""Port of src/mathOp/bmPlus.m."""

import numpy as np

from monalisa._mat import cell_from_items, cell_items, cell_shape, iscell, mixed


def bmPlus(x, y):
    """``x + y`` element-wise, also for cells of arrays."""
    if iscell(x) and iscell(y):
        pairs = zip(cell_items(x), cell_items(y), strict=True)
        return cell_from_items([mixed(np.add, a, b) for a, b in pairs], cell_shape(x))
    if not iscell(x) and not iscell(y):
        return mixed(np.add, x, y)
    raise NotImplementedError("in bmPlus: case not implemented. ")
