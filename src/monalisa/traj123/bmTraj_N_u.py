"""Port of src/traj123/bmTraj_N_u.m."""

import numpy as np

from monalisa._mat import msize
from monalisa.arrayUtility.bmPointReshape import bmPointReshape
from monalisa.traj123.bmTraj_nLine import bmTraj_nLine


def bmTraj_N_u(t):
    """Guess the Cartesian grid size ``N_u`` from the number of points per line."""
    t = bmPointReshape(t)
    imDim = msize(t, 1)
    _, N_u = bmTraj_nLine(t, nargout=2)
    if N_u < 8:
        N_u = 256.0
    return np.full((1, imDim), N_u, dtype=np.float64)
