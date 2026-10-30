"""Port of src/traj123/bmTraj_N_u_dK_u.m."""

import warnings

from monalisa._mat import isempty
from monalisa.arrayUtility.bmPointReshape import bmPointReshape
from monalisa.traj123.bmTraj_dK_u import bmTraj_dK_u
from monalisa.traj123.bmTraj_N_u import bmTraj_N_u


def bmTraj_N_u_dK_u(t, N_u=None, dK_u=None):
    """Return ``(N_u, dK_u)``, guessing the ones not given from the trajectory."""
    t = bmPointReshape(t)
    if isempty(N_u):
        warnings.warn(
            "N_u is automatically determined. You probably want to explicitly pass it as argument instead",
            stacklevel=2,
        )
        N_u = bmTraj_N_u(t)
    if isempty(dK_u):
        warnings.warn(
            "dK_u is automatically determined. You probably want to explicitly pass it as argument instead",
            stacklevel=2,
        )
        dK_u = bmTraj_dK_u(t, N_u)
    return N_u, dK_u
