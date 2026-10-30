"""Port of src/arrayUtility/bmColReshape.m."""

import numpy as np

from monalisa._mat import cell_from_items, cell_items, cell_shape, iscell, numel, reshape, vec


def bmColReshape(argIn, argSize):
    """Reshape ``argIn`` (or each element of a cell) to column shape ``[prod(argSize), nCh]``."""
    if iscell(argIn):
        return cell_from_items([bmColReshape(a, argSize) for a in cell_items(argIn)], cell_shape(argIn))
    nPt = np.prod(vec(argSize))
    nCh = numel(argIn) / nPt
    return reshape(argIn, [nPt, nCh])
