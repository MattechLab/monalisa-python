"""Port of src/geom3/bmVolumeElement_randomPartialCartesian3_x.m."""

import numpy as np

from monalisa._mat import vec
from monalisa.arrayUtility.bmPointReshape import bmPointReshape
from monalisa.geom2.bmVolumeElement_voronoi_box2 import bmVolumeElement_voronoi_box2


def bmVolumeElement_randomPartialCartesian3_x(t, N_u, dK_u):
    """Volume elements of 3D Cartesian lines along x at random (y, z) positions."""
    N_u, dK_u = vec(N_u), vec(dK_u)
    Nx = int(N_u[0])
    t = np.asarray(bmPointReshape(t))
    nLine = t.shape[1] // Nx
    t = np.reshape(t, (3, Nx, nLine), order="F")
    t1 = bmPointReshape(t[1:3, 0, :])
    ve = bmVolumeElement_voronoi_box2(t1, N_u[1:3], dK_u[1:3])
    ve = np.tile(np.ravel(ve, order="F")[None, :], (Nx, 1))
    return dK_u[0] * np.ravel(ve, order="F")[None, :]
