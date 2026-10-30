"""Port of src/traj3/bmTraj_fullRadial3_phyllotaxis_lineAssym2.m."""

import numpy as np

from monalisa._mat import fix, isempty, scalar
from monalisa.traj3.bmPhyllotaxisAngle3 import bmPhyllotaxisAngle3


def bmTraj_fullRadial3_phyllotaxis_lineAssym2(*varargin):
    """3D full-radial phyllotaxis trajectory ``[3, N, nLine]``.

    Called with an acquisition parameter object, or with
    ``(N_n, nSeg, nShot, dK_n, flagSelfNav, nShot_off)``. Self-navigation
    lines (first segment of each shot) and the first ``nShot_off`` shots are
    removed.
    """
    if len(varargin) == 0:
        raise ValueError("Wrong list of arguments. ")
    if len(varargin) == 1:
        p = varargin[0]
        N_n = scalar(p.N)
        nSeg = scalar(p.nSeg)
        nShot = scalar(p.nShot)
        dK_n = 1 / np.mean(np.ravel(p.FoV))
        flagSelfNav = bool(scalar(p.selfNav_flag))
        flagExcludeSI = flagSelfNav
        if hasattr(p, "flagExcludeSI") and not isempty(p.flagExcludeSI):
            flagExcludeSI = bool(scalar(p.flagExcludeSI))
        nShot_off = scalar(p.nShot_off)
    elif len(varargin) == 6:
        N_n, nSeg, nShot, dK_n, flagSelfNav, nShot_off = (scalar(a) for a in varargin)
        flagExcludeSI = None
    else:
        raise ValueError("Wrong list of arguments. ")
    if fix(N_n / 2) != N_n / 2:
        raise ValueError("N_n must be even in 'bm3DimRadialTraj_phyllotaxis_2' ! ")
    N_n, nSeg, nShot, nShot_off = int(N_n), int(nSeg), int(nShot), int(nShot_off)

    theta, phi = bmPhyllotaxisAngle3(nSeg, nShot, flagSelfNav)
    r = -0.5 + np.arange(N_n) * (1 / N_n)
    phi = np.tile(phi, (N_n, 1))
    theta = np.tile(theta, (N_n, 1))
    R = np.tile(r[:, None], (1, nShot * nSeg))
    shape = (1, N_n, nSeg, nShot)
    x = np.reshape(R * np.cos(phi) * np.sin(theta), shape, order="F")
    y = np.reshape(R * np.sin(phi) * np.sin(theta), shape, order="F")
    z = np.reshape(R * np.cos(theta), shape, order="F")
    myTraj = np.concatenate([x, y, z], axis=0) * N_n * dK_n
    if flagExcludeSI:
        myTraj = myTraj[:, :, 1:, :]
    if nShot_off > 0:
        myTraj = myTraj[:, :, :, nShot_off:]
    s = myTraj.shape
    return np.reshape(myTraj, (s[0], s[1], s[2] * s[3]), order="F")
