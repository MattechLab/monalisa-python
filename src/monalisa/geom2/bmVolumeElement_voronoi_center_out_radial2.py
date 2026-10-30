"""Port of src/geom2/bmVolumeElement_voronoi_center_out_radial2.m."""

import numpy as np

from monalisa._mat import msize
from monalisa.geom1.bmVolumeElement1 import bmVolumeElement1
from monalisa.geom123.bmVoronoi import bmVoronoi
from monalisa.traj123.bmTraj_formatTraj import bmTraj_formatTraj
from monalisa.traj123.bmTraj_lineDirection import bmTraj_lineDirection
from monalisa.traj123.bmTraj_lineReshape import bmTraj_lineReshape
from monalisa.traj123.bmTraj_norm import bmTraj_norm


def _radial_dr(t3, centerFlag):
    """Radial spacing of center-out lines (first sample from the center)."""
    imDim, N, nLine = t3.shape
    e = np.reshape(bmTraj_lineDirection(t3), (imDim, nLine), order="F")
    dr = np.zeros((N, nLine))
    for i in range(nLine):
        dr[:, i] = t3[:, :, i].T @ e[:, i]
    dr = bmVolumeElement1(dr)
    r_1 = np.zeros(nLine)
    r_2 = np.zeros(nLine)
    for i in range(imDim):
        r_1 = r_1 + t3[i, 0, :] ** 2
        r_2 = r_2 + t3[i, 1, :] ** 2
    r_1, r_2 = np.sqrt(r_1), np.sqrt(r_2)
    dr[0, :] = r_2 / 2 if centerFlag else (r_1 + r_2) / 2
    return dr, e, r_1


def bmVolumeElement_voronoi_center_out_radial2(t):
    """Volume elements of a 2D center-out radial trajectory."""
    if msize(t, 1) != 2:
        raise ValueError("The trajectory must be 2Dim. ")
    t, _, formatedIndex, formatedWeight = bmTraj_formatTraj(t, nargout=4)
    centerFlag = np.linalg.norm(t[:, 0]) < 100 * np.finfo(np.float64).eps
    if centerFlag:
        t = t[:, 1:]
    t = bmTraj_lineReshape(t)
    N, nLine = msize(t, 2), msize(t, 3)
    t3 = np.reshape(t, (2, N, nLine), order="F")
    dr, e, r_1 = _radial_dr(t3, centerFlag)
    myAngle = np.arctan2(e[1, :], e[0, :])
    myPerm = np.argsort(myAngle, kind="stable")
    myAngle = myAngle[myPerm]
    myInvPerm = np.argsort(myPerm, kind="stable")
    myCutSpace = (np.pi - myAngle[-1]) + (myAngle[0] + np.pi)
    v1 = (myAngle[1] - myAngle[0]) / 2 + myCutSpace / 2
    vend = (myAngle[-1] - myAngle[-2]) / 2 + myCutSpace / 2
    av = np.ravel(bmVoronoi(myAngle[None, :]), order="F").copy()
    av[0], av[-1] = v1, vend
    av = np.tile(av[myInvPerm], (N, 1))
    ds = np.reshape(bmTraj_norm(t), (N, nLine), order="F") * av
    v = np.ravel(dr, order="F") * np.ravel(ds, order="F")
    if centerFlag:
        dr_0 = np.mean(r_1 / 2)
        v = np.concatenate([[np.pi * dr_0**2], v])
    idx = np.ravel(formatedIndex).astype(np.int64) - 1
    return (v[idx] * np.ravel(formatedWeight))[None, :]
