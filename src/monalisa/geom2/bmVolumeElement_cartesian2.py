"""Port of src/geom2/bmVolumeElement_cartesian2.m."""

import numpy as np

from monalisa._mat import msize
from monalisa.arrayUtility.bmPointReshape import bmPointReshape
from monalisa.traj123.bmTraj_squaredNorm import bmTraj_squaredNorm


def _farthest(t, c):
    return t[:, int(np.argmax(np.ravel(bmTraj_squaredNorm(c[:, None] - t))))]


def bmVolumeElement_cartesian2(t):
    """Volume element of a (possibly rotated) 2D Cartesian grid: product of the
    grid steps along the grid axes, the same for all points."""
    if msize(t, 1) != 2:
        raise ValueError("The trajectory must be 2Dim")
    t = np.asarray(bmPointReshape(t), dtype=np.float64)
    nPt = t.shape[1]
    c1 = _farthest(t, t[:, 0])
    c2 = _farthest(t, c1)
    p_c1 = t - c1[:, None]
    e = (c2 - c1) / np.linalg.norm(c2 - c1)
    s = e @ p_c1
    myDiff = p_c1 - s[None, :] * e[:, None]
    c3 = t[:, int(np.argmax(np.ravel(bmTraj_squaredNorm(myDiff))))]
    c4 = _farthest(t, c3)
    b3 = (c3 - c1) / np.linalg.norm(c3 - c1)
    b4 = (c4 - c1) / np.linalg.norm(c4 - c1)
    t = np.linalg.inv(np.column_stack([b3, b4])) @ t
    dK = []
    for k in range(2):
        d = np.diff(np.sort(t[k, :]))
        dK.append(np.mean(d[d > np.max(d) / 3]))
    return dK[0] * dK[1] * np.ones((1, nPt))
