"""Port of src/traj123/bmTraj_squaredNorm.m."""

import numpy as np

from monalisa._mat import msize, reshape
from monalisa.array._point_reshape import point_reshape


def traj_squared_norm(t):
    """Squared norm of each trajectory point, shaped ``[1, size(t)(2:end)]``."""
    mySize = msize(t)
    t = np.asarray(point_reshape(t))
    dt = t.dtype if t.dtype in (np.float32, np.float64) else np.float64
    mySquaredNorm = np.zeros(t.shape[1], dtype=dt)
    for i in range(mySize[0]):
        mySquaredNorm = mySquaredNorm + t[i, :] ** 2
    return reshape(mySquaredNorm, [1, *mySize[1:]])
