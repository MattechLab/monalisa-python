"""Port of src/geom3/bmVolumeElement_full_radial3.m."""

import numpy as np

from monalisa._mat import fix, msize
from monalisa.geom1.bmVolumeElement1 import bmVolumeElement1
from monalisa.traj123.bmTraj_lineDirection import bmTraj_lineDirection
from monalisa.traj123.bmTraj_lineReshape import bmTraj_lineReshape
from monalisa.traj123.bmTraj_squaredNorm import bmTraj_squaredNorm


def bmVolumeElement_full_radial3(t):
    """Volume elements of a 3D full-radial trajectory assuming uniformly spread lines."""
    if msize(t, 1) != 3:
        raise ValueError("The trajectory must be 3Dim. ")
    t = bmTraj_lineReshape(t)
    N, nLine = msize(t, 2), msize(t, 3)
    t3 = np.reshape(t, (3, N, nLine), order="F")
    e = np.reshape(bmTraj_lineDirection(t), (3, nLine), order="F")
    if (N / 2 - fix(N / 2)) > 0:
        raise ValueError(
            "The number of points per line must be even, because the 0 must be at index position N/2+1"
        )
    dr = np.zeros((N, nLine))
    for i in range(nLine):
        dr[:, i] = t3[:, :, i].T @ e[:, i]
    dr = bmVolumeElement1(dr)
    ds = np.reshape(4 * np.pi * bmTraj_squaredNorm(t) / (2 * nLine), (N, nLine), order="F")
    v = (np.ravel(dr, order="F") * np.ravel(ds, order="F"))[None, :]
    dr_0 = np.mean(dr[N // 2, :]) / 2
    v[0, N // 2 :: N] = (4 / 3) * np.pi * dr_0**3 / (2 * nLine)
    return v
