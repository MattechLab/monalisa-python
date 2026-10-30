"""Port of src/geom3/bmVolumeElement_center_out_radial3.m."""

import numpy as np

from monalisa._mat import msize
from monalisa.geom2.bmVolumeElement_voronoi_center_out_radial2 import _radial_dr
from monalisa.traj123.bmTraj_formatTraj import bmTraj_formatTraj
from monalisa.traj123.bmTraj_lineReshape import bmTraj_lineReshape
from monalisa.traj123.bmTraj_squaredNorm import bmTraj_squaredNorm


def bmVolumeElement_center_out_radial3(t):
    """Volume elements of a 3D center-out radial trajectory (uniform solid angle)."""
    if msize(t, 1) != 3:
        raise ValueError("The trajectory must be 3Dim")
    t, _, formatedIndex, formatedWeight = bmTraj_formatTraj(t, nargout=4)
    centerFlag = np.linalg.norm(t[:, 0]) < 100 * np.finfo(np.float64).eps
    if centerFlag:
        t = t[:, 1:]
    t = bmTraj_lineReshape(t)
    N, nLine = msize(t, 2), msize(t, 3)
    t3 = np.reshape(t, (3, N, nLine), order="F")
    dr, _, r_1 = _radial_dr(t3, centerFlag)
    ds = np.reshape(4 * np.pi * bmTraj_squaredNorm(t) / nLine, (N, nLine), order="F")
    v = np.ravel(dr, order="F") * np.ravel(ds, order="F")
    if centerFlag:
        dr_0 = np.mean(r_1 / 2)
        v = np.concatenate([[(4 / 3) * np.pi * dr_0**3], v])
    idx = np.ravel(formatedIndex).astype(np.int64) - 1
    return (v[idx] * np.ravel(formatedWeight))[None, :]
