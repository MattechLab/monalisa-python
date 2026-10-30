"""Port of src/geom1/bmVolumeElement1.m."""

import numpy as np

from monalisa._mat import col, msize


def bmVolumeElement1(x):
    """1D Voronoi lengths of the samples ``x`` (columns sorted by the first column)."""
    x = np.asarray(x)
    if msize(x, 1) == 1 or msize(x, 2) == 1:
        x = col(x)
    myPerm = np.argsort(x[:, 0], kind="stable")
    myInvPerm = np.argsort(myPerm, kind="stable")
    mySort = x[myPerm, :]
    myMid = (mySort[1:, :] + mySort[:-1, :]) / 2
    myMid = np.concatenate(
        [
            mySort[0:1, :] - (myMid[0:1, :] - mySort[0:1, :]),
            myMid,
            mySort[-1:, :] + (mySort[-1:, :] - myMid[-1:, :]),
        ],
        axis=0,
    )
    myDiff = myMid[1:, :] - myMid[:-1, :]
    return myDiff[myInvPerm, :]
