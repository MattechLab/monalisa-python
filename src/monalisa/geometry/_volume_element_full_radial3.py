"""Port of src/geom3/bmVolumeElement_full_radial3.m."""

import numpy as np

from monalisa._mat import fix, msize
from monalisa.geometry._volume_element1 import volume_element1
from monalisa.trajectory._traj_line_direction import traj_line_direction
from monalisa.trajectory._traj_line_reshape import traj_line_reshape
from monalisa.trajectory._traj_squared_norm import traj_squared_norm


def volume_element_full_radial3(t):
    """Volume elements of a 3D full-radial trajectory assuming uniformly spread lines."""
    if msize(t, 1) != 3:
        raise ValueError("The trajectory must be 3Dim. ")
    t = traj_line_reshape(t)
    N, nLine = msize(t, 2), msize(t, 3)
    t3 = np.reshape(t, (3, N, nLine), order="F")
    e = np.reshape(traj_line_direction(t), (3, nLine), order="F")
    if (N / 2 - fix(N / 2)) > 0:
        raise ValueError(
            "The number of points per line must be even, because the 0 must be at index position N/2+1"
        )
    dr = np.zeros((N, nLine))
    for i in range(nLine):
        dr[:, i] = t3[:, :, i].T @ e[:, i]
    dr = volume_element1(dr)
    ds = np.reshape(4 * np.pi * traj_squared_norm(t) / (2 * nLine), (N, nLine), order="F")
    v = (np.ravel(dr, order="F") * np.ravel(ds, order="F"))[None, :]
    dr_0 = np.mean(dr[N // 2, :]) / 2
    v[0, N // 2 :: N] = (4 / 3) * np.pi * dr_0**3 / (2 * nLine)
    return v
