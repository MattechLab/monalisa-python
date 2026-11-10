"""Port of src/geom2/bmVolumeElement_voronoi_center_out_radial2.m."""

import numpy as np

from monalisa._mat import msize
from monalisa.geometry._volume_element1 import volume_element1
from monalisa.geometry._voronoi import voronoi
from monalisa.trajectory._traj_format import traj_format
from monalisa.trajectory._traj_line_direction import traj_line_direction
from monalisa.trajectory._traj_line_reshape import traj_line_reshape
from monalisa.trajectory._traj_norm import traj_norm


def _radial_dr(t3, centerFlag):
    """Radial spacing of center-out lines (first sample from the center)."""
    imDim, N, nLine = t3.shape
    e = np.reshape(traj_line_direction(t3), (imDim, nLine), order="F")
    dr = np.zeros((N, nLine))
    for i in range(nLine):
        dr[:, i] = t3[:, :, i].T @ e[:, i]
    dr = volume_element1(dr)
    r_1 = np.zeros(nLine)
    r_2 = np.zeros(nLine)
    for i in range(imDim):
        r_1 = r_1 + t3[i, 0, :] ** 2
        r_2 = r_2 + t3[i, 1, :] ** 2
    r_1, r_2 = np.sqrt(r_1), np.sqrt(r_2)
    dr[0, :] = r_2 / 2 if centerFlag else (r_1 + r_2) / 2
    return dr, e, r_1


def volume_element_voronoi_center_out_radial2(t):
    """Volume elements of a 2D center-out radial trajectory."""
    if msize(t, 1) != 2:
        raise ValueError("The trajectory must be 2Dim. ")
    t, _, formatedIndex, formatedWeight = traj_format(t, nargout=4)
    centerFlag = np.linalg.norm(t[:, 0]) < 100 * np.finfo(np.float64).eps
    if centerFlag:
        t = t[:, 1:]
    t = traj_line_reshape(t)
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
    av = np.ravel(voronoi(myAngle[None, :]), order="F").copy()
    av[0], av[-1] = v1, vend
    av = np.tile(av[myInvPerm], (N, 1))
    ds = np.reshape(traj_norm(t), (N, nLine), order="F") * av
    v = np.ravel(dr, order="F") * np.ravel(ds, order="F")
    if centerFlag:
        dr_0 = np.mean(r_1 / 2)
        v = np.concatenate([[np.pi * dr_0**2], v])
    idx = np.ravel(formatedIndex).astype(np.int64) - 1
    return (v[idx] * np.ravel(formatedWeight))[None, :]
