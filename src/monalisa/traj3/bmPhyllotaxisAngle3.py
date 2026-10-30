"""Port of src/traj3/bmPhyllotaxisAngle3.m."""

import numpy as np


def bmPhyllotaxisAngle3(nseg, nshot, flagSelfNav=0):
    """Polar ``theta`` and azimuthal ``phi`` angles (rows of length ``nseg*nshot``)
    of the 3D golden-angle phyllotaxis spiral; with ``flagSelfNav`` the first
    segment of each shot points along z (theta = phi = 0)."""
    nseg = int(nseg)
    nshot = int(nshot)
    goldNum = (1 + np.sqrt(5)) / 2
    goldAngle = 2 * np.pi - (2 * np.pi / goldNum)
    nseg_tot = nseg * nshot
    nseg_pure = nseg_tot - nshot if flagSelfNav else nseg_tot
    q = np.pi / (2 * np.sqrt(nseg_pure))
    phi = np.zeros((1, nseg_tot))
    theta = np.zeros((1, nseg_tot))
    i, j = np.meshgrid(np.arange(1, nseg + 1), np.arange(1, nshot + 1), indexing="ij")
    i = i.ravel()  # loop order: i outer, j inner
    j = j.ravel()
    myIndex = i + (j - 1) * nseg - 1
    nav = (i == 1) if flagSelfNav else np.zeros(i.size, dtype=bool)
    myCounter = np.cumsum(~nav).astype(np.float64)
    pure = ~nav
    phi[0, myIndex[pure]] = np.mod(myCounter[pure] * goldAngle, 2 * np.pi)
    theta[0, myIndex[pure]] = q * np.sqrt(myCounter[pure])
    return theta, phi
