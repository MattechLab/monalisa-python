"""Port of src/geom3/bmVolumeElement_voronoi_full_radial3.m."""

import numpy as np

from monalisa._mat import fix, msize, squeeze
from monalisa.geom1.bmVolumeElement1 import bmVolumeElement1
from monalisa.geom123.bmVoronoi import bmVoronoi
from monalisa.traj123.bmTraj_lineDirection import bmTraj_lineDirection
from monalisa.traj123.bmTraj_lineReshape import bmTraj_lineReshape
from monalisa.traj123.bmTraj_squaredNorm import bmTraj_squaredNorm


def bmVolumeElement_voronoi_full_radial3(t):
    """Volume elements of a 3D full-radial trajectory (radial x spherical Voronoi)."""
    if msize(t, 1) != 3:
        raise ValueError("This function is for 3D trajectory only. ")
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

    ds = _spherical_voronoi_1(t3, "half")
    ds = np.tile(ds, (N, 1))
    ds = ds * np.reshape(squeeze(bmTraj_squaredNorm(t)), (N, nLine), order="F")
    v = (np.ravel(dr, order="F") * np.ravel(ds, order="F"))[None, :]
    dr_0 = np.mean(dr[N // 2, :]) / 2
    v[0, N // 2 :: N] = (4 / 3) * np.pi * (dr_0**3) / (2 * nLine)
    return v


def _spherical_voronoi_1(t3, half_or_full):
    """Solid angle of the line directions (local function bmSphericalVoronoi_1)."""
    imDim, _, nLine = t3.shape
    s = t3[:, -1, :]
    s_norm = np.zeros(s.shape[1], dtype=s.dtype)
    for i in range(imDim):
        s_norm = s_norm + s[i, :] ** 2
    s = s / np.sqrt(s_norm)[None, :]
    if half_or_full == "half":
        s = np.concatenate([s, -s], axis=1)

    caps = [
        (s[0, :] >= 0, (2, 1, 0), 1.0),
        (s[0, :] <= 0, (2, 1, 0), -1.0),
        (s[1, :] >= 0, (2, 0, 1), 1.0),
        (s[1, :] <= 0, (2, 0, 1), -1.0),
        (s[2, :] >= 0, (0, 1, 2), 1.0),
        (s[2, :] <= 0, (0, 1, 2), -1.0),
    ]
    v = np.zeros((6, s.shape[1]))
    for k, (mask, (a, b, c), sign) in enumerate(caps):
        sc = s[:, mask]
        v[k, mask] = _spherical_voronoi_2(sc[a, :], sc[b, :], sign * sc[c, :])
    v = v[:, :nLine]
    myWeight = v > 0
    with np.errstate(invalid="ignore", divide="ignore"):
        return (np.sum(v, axis=0) / np.sum(myWeight, axis=0))[None, :]


def _spherical_voronoi_2(s1, s2, s3):
    """Voronoi areas on the cap around +z after gnomonic projection (bmSphericalVoronoi_2)."""
    s = np.stack([s1, s2, s3])
    nPt = s.shape[1]
    myIndex = np.arange(nPt)
    myAngle = np.arccos(1 / np.sqrt(3))
    myAngle = (np.pi / 2 - myAngle) / 3
    h1 = np.sin(1 * myAngle)
    h2 = np.sin(2 * myAngle)
    myMask_1 = s[2, :] < h1
    s = s[:, ~myMask_1]
    myIndex = myIndex[~myMask_1]
    myMask_2 = s[2, :] < h2
    p = s[0:2, :] / s[2, :][None, :]
    myVoronoi = np.ravel(bmVoronoi(p), order="F").copy()
    myVoronoi[myVoronoi <= 0] = 0
    myVoronoi[myMask_2] = 0
    myVoronoi = myVoronoi * np.abs(s[2, :] ** 3)
    out = np.zeros(nPt)
    out[myIndex] = myVoronoi
    return out
