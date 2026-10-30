"""Port of src/traj123/bmTraj_dK_u.m."""

import numpy as np

from monalisa._mat import isempty, msize, vec
from monalisa.arrayUtility.bmPointReshape import bmPointReshape
from monalisa.traj123.bmTraj_N_u import bmTraj_N_u
from monalisa.traj123.bmTraj_nLine import bmTraj_nLine


def _dK_n(t):
    _, _, _, dK_n = bmTraj_nLine(t, nargout=4)
    dK_n = dK_n.ravel()
    med = np.median(dK_n)
    dK_n = dK_n[~(dK_n > 2 * med)]
    dK_n = dK_n[~(dK_n < 0.5 * med)]
    return np.median(dK_n)


def bmTraj_dK_u(t, N_u=None):
    """Guess the Cartesian grid step ``dK_u`` from the trajectory extent."""
    if isempty(N_u):
        N_u = bmTraj_N_u(t)
    N_u = vec(N_u)
    t = np.asarray(bmPointReshape(t))
    imDim = msize(t, 1)
    dK = [abs(t[i, :].max() - t[i, :].min()) / (N_u[i] - 1) for i in range(imDim)]
    if imDim == 2:
        if abs(dK[0] - dK[1]) / max(dK[0], dK[1]) < 0.02:
            dK = [_dK_n(t)] * 2
    elif imDim == 3:
        d = [abs(dK[0] - dK[1]) / max(dK[0], dK[1]),
             abs(dK[1] - dK[2]) / max(dK[1], dK[2]),
             abs(dK[2] - dK[0]) / max(dK[2], dK[0])]
        if max(d) < 0.02:
            dK = [_dK_n(t)] * 3
    return np.array([dK], dtype=np.result_type(*dK, np.float32))
