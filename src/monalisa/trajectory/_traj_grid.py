"""Port of src/traj123/bmTraj_N_u_dK_u.m."""

import warnings

from monalisa._mat import isempty
from monalisa.array._point_reshape import point_reshape
from monalisa.trajectory._traj_grid_size import traj_grid_size
from monalisa.trajectory._traj_grid_step import traj_grid_step


def traj_grid(t, N_u=None, dK_u=None):
    """Return ``(N_u, dK_u)``, guessing the ones not given from the trajectory."""
    t = point_reshape(t)
    if isempty(N_u):
        warnings.warn(
            "N_u is automatically determined. You probably want to explicitly pass it as argument instead",
            stacklevel=2,
        )
        N_u = traj_grid_size(t)
    if isempty(dK_u):
        warnings.warn(
            "dK_u is automatically determined. You probably want to explicitly pass it as argument instead",
            stacklevel=2,
        )
        dK_u = traj_grid_step(t, N_u)
    return N_u, dK_u
