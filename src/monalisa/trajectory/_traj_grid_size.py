"""Port of src/traj123/bmTraj_N_u.m."""

import numpy as np

from monalisa._mat import msize
from monalisa.array._point_reshape import point_reshape
from monalisa.trajectory._traj_n_line import traj_n_line


def traj_grid_size(t):
    """Guess the Cartesian grid size ``N_u`` from the number of points per line."""
    t = point_reshape(t)
    imDim = msize(t, 1)
    _, N_u = traj_n_line(t, nargout=2)
    if N_u < 8:
        N_u = 256.0
    return np.full((1, imDim), N_u, dtype=np.float64)
