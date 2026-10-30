"""Port of src/geom2/bmVolumeElement_randomPartialCartesian2_x.m."""

import numpy as np

from monalisa._mat import vec
from monalisa.arrayUtility.bmPointReshape import bmPointReshape
from monalisa.geom1.bmVolumeElement1 import bmVolumeElement1


def bmVolumeElement_randomPartialCartesian2_x(t, N_u, dK_u):
    """Volume elements of 2D Cartesian lines along x at random y positions."""
    N_u, dK_u = vec(N_u), vec(dK_u)
    Nx = int(N_u[0])
    t = np.asarray(bmPointReshape(t))
    nLine = t.shape[1] // Nx
    t = np.reshape(t, (2, Nx, nLine), order="F")
    ve = bmVolumeElement1(bmPointReshape(t[1, 0, :]))
    ve = np.tile(np.ravel(ve, order="F")[None, :], (Nx, 1))
    return dK_u[0] * np.ravel(ve, order="F")[None, :]
