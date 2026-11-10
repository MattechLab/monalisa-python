"""Port of src/arrayUtility/bmBlockReshape.m."""

import numpy as np

from monalisa._mat import cell_from_items, cell_items, cell_shape, iscell, isempty, numel, reshape, vec


def block_reshape(argIn, N_u):
    """Reshape ``argIn`` (or each element of a cell) to block shape ``[N_u, nCh]``.

    ``nCh = numel(argIn) / prod(N_u)``; MATLAB drops the trailing ``nCh`` when
    it equals 1. Returns ``None`` (MATLAB ``[]``) for empty input.
    """
    if iscell(argIn):
        return cell_from_items([block_reshape(a, N_u) for a in cell_items(argIn)], cell_shape(argIn))
    if isempty(argIn):
        return None
    N_u = vec(N_u)
    nCh = numel(argIn) / np.prod(N_u)
    return reshape(argIn, [*N_u, nCh])
