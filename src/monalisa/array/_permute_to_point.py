"""Port of src/arrayUtility/bmPermuteToPoint.m."""

import numpy as np

from monalisa._mat import cell_from_items, cell_items, cell_shape, iscell, isempty, numel, reshape, vec


def permute_to_point(y, argSize):
    """Column format ``[nPt, nCh]`` -> point format ``[nCh, nPt]``, ``nPt = prod(argSize)``."""
    if iscell(y):
        return cell_from_items([permute_to_point(a, argSize) for a in cell_items(y)], cell_shape(y))
    if isempty(y):
        return None
    nPt = np.prod(vec(argSize))
    return reshape(y, [nPt, numel(y) / nPt]).T
