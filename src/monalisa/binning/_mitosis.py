"""Port of src/arrayUtility/bmMitosis.m."""

import numpy as np

from monalisa._mat import cell_from_items, cell_items, iscell, msize, reshape
from monalisa.array._index_to_multi_index import index_to_multi_index


def mitosis(*varargin, nargout=2):
    """Split ``nargout`` tables (last dimension = samples) into bins.

    The remaining arguments are 2D logical masks ``[nPhase, nSample]`` (or one
    cell of them); every combination of one phase per mask is a bin. Returns
    one ``[N_tot, 1]`` cell per table.
    """
    nTable = nargout
    nMask = len(varargin) - nTable
    if nTable < 1 or nMask < 1:
        raise ValueError("Wrong list of argumnts")
    tables = [np.asarray(a) for a in varargin[:nTable]]
    nOfCol = msize(tables[0])[-1]
    in_size, new_size = [], []
    for tab in tables:
        s = msize(tab)
        if s[-1] != nOfCol:
            raise ValueError("The last dimension is not the same for every input array. ")
        in_size.append(list(s[:-1]))
        new_size.append((int(np.prod(s[:-1])), s[-1]))
    if iscell(varargin[nTable]):
        mask_list = cell_items(varargin[nTable])
    else:
        mask_list = list(varargin[nTable:])
    for m in mask_list:
        if msize(m)[-1] != nOfCol:
            raise ValueError("The last dimension is not the same for every input array. ")
        if len(msize(m)) != 2:
            raise ValueError("The masks must be 2Dim. ")
    inTable = [np.reshape(t, ns, order="F") for t, ns in zip(tables, new_size, strict=True)]
    masks = [np.asarray(m, dtype=bool) for m in mask_list]
    nPhase = np.array([m.shape[0] for m in masks], dtype=np.float64)
    N_tot = int(np.prod(nPhase))
    out = [[None] * N_tot for _ in range(nTable)]
    for i in range(N_tot):
        myIndex = index_to_multi_index(i + 1, nPhase).ravel().astype(np.int64) - 1
        myMask = np.ones(nOfCol, dtype=bool)
        for k, m in enumerate(masks):
            myMask &= m[myIndex[k], :]
        for j in range(nTable):
            out[j][i] = reshape(inTable[j][:, myMask], [*in_size[j], int(myMask.sum())])
    cells = tuple(cell_from_items(o, (N_tot, 1)) for o in out)
    return cells[0] if nTable == 1 else cells
