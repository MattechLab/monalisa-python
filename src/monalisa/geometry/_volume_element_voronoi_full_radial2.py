"""Port of src/geom2/bmVolumeElement_voronoi_full_radial2.m."""

import numpy as np

from monalisa._mat import fix, msize, squeeze
from monalisa.geometry._volume_element1 import volume_element1
from monalisa.geometry._voronoi import voronoi
from monalisa.trajectory._traj_line_direction import traj_line_direction
from monalisa.trajectory._traj_line_reshape import traj_line_reshape
from monalisa.trajectory._traj_norm import traj_norm


def volume_element_voronoi_full_radial2(t):
    """Volume elements of a 2D full-radial trajectory (radial x angular Voronoi)."""
    if msize(t, 1) != 2:
        raise ValueError("The trajectory must be 2Dim")
    t = traj_line_reshape(t)
    N, nLine = msize(t, 2), msize(t, 3)
    t3 = np.reshape(t, (2, N, nLine), order="F")
    e = np.reshape(traj_line_direction(t), (2, nLine), order="F")
    if (N / 2 - fix(N / 2)) > 0:
        raise ValueError(
            "The number of points per line must be even, because the 0 must be at index position N/2+1"
        )

    dr = np.zeros((N, nLine))
    for i in range(nLine):
        dr[:, i] = t3[:, :, i].T @ e[:, i]
    dr = volume_element1(dr)

    ee = np.concatenate([e, -e], axis=1)
    myAngle = np.arctan2(ee[1, :], ee[0, :])
    myPerm = np.argsort(myAngle, kind="stable")
    myAngle = myAngle[myPerm]
    myInvPerm = np.argsort(myPerm, kind="stable")
    myCutSpace = (np.pi - myAngle[-1]) + (myAngle[0] - (-np.pi))
    myVoronoi_1 = (myAngle[1] - myAngle[0]) / 2 + myCutSpace / 2
    myVoronoi_end = (myAngle[-1] - myAngle[-2]) / 2 + myCutSpace / 2
    myAngleVoronoi = np.ravel(voronoi(myAngle[None, :]), order="F").copy()
    myAngleVoronoi[0] = myVoronoi_1
    myAngleVoronoi[-1] = myVoronoi_end
    myAngleVoronoi = myAngleVoronoi[myInvPerm][:nLine]
    myAngleVoronoi = np.tile(myAngleVoronoi, (N, 1))

    ds = squeeze(traj_norm(t)) * myAngleVoronoi
    v = (np.ravel(dr, order="F") * np.ravel(ds, order="F"))[None, :]
    dr_0 = np.mean(dr[N // 2, :]) / 2
    v0 = np.pi * (dr_0**2) / (2 * nLine)
    v[0, N // 2 :: N] = v0
    return v
