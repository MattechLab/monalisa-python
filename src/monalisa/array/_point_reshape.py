"""Port of src/arrayUtility/bmPointReshape.m."""

import numpy as np

from monalisa._mat import (
    cell_from_items,
    cell_items,
    cell_shape,
    iscell,
    isempty,
    msize,
    ndims,
    numel,
    reshape,
    row,
    vec,
)


def point_reshape(t, argSize=None):
    """Reshape ``t`` to point format ``[nCh, nPt]``.

    Vectors become row vectors. ``nCh`` is ``argSize[0]`` when given, else
    ``size(t, 1)``.
    """
    if iscell(t):
        return cell_from_items([point_reshape(a, argSize) for a in cell_items(t)], cell_shape(t))
    t = np.asarray(t)
    if ndims(t) == 2 and (msize(t, 1) == 1 or msize(t, 2) == 1):
        return row(t)
    nCh = msize(t, 1) if isempty(argSize) else vec(argSize)[0]
    nPt = numel(t) / nCh
    return reshape(t, [nCh, nPt])
