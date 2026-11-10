"""Port of src/arrayUtility/bmPermuteToCol.m."""

import numpy as np

from monalisa._mat import cell_from_items, cell_items, cell_shape, iscell, isempty, msize, numel, reshape, vec


def permute_to_col(y, argSize=None):
    """Reshape data ``[nCh, ...]`` to ``[nCh, nPt]`` and transpose to column format ``[nPt, nCh]``."""
    if iscell(y):
        return cell_from_items([permute_to_col(a, argSize) for a in cell_items(y)], cell_shape(y))
    if isempty(y):
        return None
    if isempty(argSize):
        nCh = msize(y, 1)
        nPt = numel(y) / nCh
    else:
        nPt = np.prod(vec(argSize))
        nCh = numel(y) / nPt
    return reshape(y, [nCh, nPt]).T
