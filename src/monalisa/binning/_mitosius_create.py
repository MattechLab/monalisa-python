"""Port of src/mitosius/bmMitosius_create.m."""

import os

import numpy as np

from monalisa._mat import cell_items, cell_shape
from monalisa.array._index_to_multi_index import index_to_multi_index
from monalisa.io._create_dir import create_dir
from monalisa.io._mat73 import savemat73


def mitosius_create(mitosius_dir, *varargin):
    """Write binned data to ``mitosius_dir/cell_<i>[_<j>...]/{y,t,ve}.mat`` (MATLAB v7.3)
    and ``mitosius_size.mat``. Arguments: ``(y_cell, t_cell, ve_cell)`` or ``(mitosius_length,)``."""
    y_cell = t_cell = ve_cell = None
    mitosius_size = None
    if len(varargin) == 1:
        mitosius_length = int(np.asarray(varargin[0]).item())
    elif len(varargin) == 3:
        y_cell, t_cell, ve_cell = varargin
        mitosius_size = np.array([cell_shape(y_cell)], dtype=np.float64)
        mitosius_length = int(np.prod(mitosius_size))
    else:
        raise ValueError("Wrong list of arguments. ")
    create_dir(mitosius_dir)
    named = (("y", y_cell), ("t", t_cell), ("ve", ve_cell))
    items = {k: (None if c is None else cell_items(c)) for k, c in named}
    for i in range(mitosius_length):
        idx = []
        if mitosius_size is not None:
            idx = index_to_multi_index(i + 1, mitosius_size).ravel().astype(np.int64)
        cell_dir = os.path.join(mitosius_dir, "cell" + "".join(f"_{k}" for k in idx))
        create_dir(cell_dir)
        for name, vals in items.items():
            if vals is not None:
                savemat73(os.path.join(cell_dir, f"{name}.mat"), {name: vals[i]})
    savemat73(os.path.join(mitosius_dir, "mitosius_size.mat"), {"mitosius_size": mitosius_size})
