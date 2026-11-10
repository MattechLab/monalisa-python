"""Port of src/varargin/bmVarargin_N_u_dK_u.m."""

from monalisa._mat import double, single
from monalisa.trajectory._traj_grid import traj_grid


def default_grid(t, N_u=None, dK_u=None):
    """Return ``(N_u, dK_u)`` (guessed from ``t`` when missing), rounded through single."""
    N_u, dK_u = traj_grid(t, N_u, dK_u)
    return double(single(N_u)), double(single(dK_u))
