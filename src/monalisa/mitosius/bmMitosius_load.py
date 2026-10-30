"""Port of src/mitosius/bmMitosius_load.m."""

import os

import numpy as np

from monalisa._mat import cell_from_items, squeeze
from monalisa.arrayUtility.bmIndex2MultiIndex import bmIndex2MultiIndex
from monalisa.readWrite._mat73 import loadmat73


def _load_var(path):
    try:
        data = loadmat73(path)
    except OSError:  # non-HDF5 MAT-file
        import scipy.io as sio

        data = {k: v for k, v in sio.loadmat(path).items() if not k.startswith("__")}
    return next(iter(data.values()))


def bmMitosius_load(mitosius_dir, arg_name, *edges):
    """Load the variable ``arg_name`` of every cell (or of the cells selected by
    ``edges``: 1-based indices or ``'all'`` per mitosius dimension)."""
    in_size = np.ravel(_load_var(os.path.join(mitosius_dir, "mitosius_size.mat"))).astype(np.int64)
    ndim = in_size.size
    if not edges:
        edge_list = [np.arange(1, n + 1) for n in in_size]
    else:
        if len(edges) != ndim:
            raise ValueError("The number of edges not compatible with mitosius_ndims. ")
        edge_list = []
        for i, e in enumerate(edges):
            if isinstance(e, str):
                if e != "all":
                    raise ValueError("Wrong input arguments. ")
                e = np.arange(1, in_size[i] + 1)
            edge_list.append(np.ravel(np.asarray(e)).astype(np.int64))
    out_size = np.array([e.size for e in edge_list], dtype=np.float64)
    items = []
    for i in range(int(np.prod(out_size))):
        outIdx = bmIndex2MultiIndex(i + 1, out_size).ravel().astype(np.int64) - 1
        inIdx = [edge_list[j][outIdx[j]] for j in range(ndim)]
        name = "cell" + "".join(f"_{k}" for k in inIdx)
        items.append(_load_var(os.path.join(mitosius_dir, name, f"{arg_name}.mat")))
    shape = [int(s) for s in out_size]
    if len(shape) == 1:
        shape = [shape[0], 1]
    out = cell_from_items(items, shape)
    sq = squeeze(np.empty(out.shape, dtype=object))
    return np.reshape(out, sq.shape, order="F")
