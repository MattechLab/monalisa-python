"""Port of src/traj123/bmTraj_norm.m."""

import numpy as np

from monalisa._mat import msize, reshape
from monalisa.array._point_reshape import point_reshape


def traj_norm(t):
    """Euclidean norm of each trajectory point, shaped like ``size(t)(2:end)``."""
    mySize = msize(t)
    t = np.asarray(point_reshape(t))
    dt = t.dtype if t.dtype in (np.float32, np.float64) else np.float64
    myNorm = np.zeros(t.shape[1], dtype=dt)
    for i in range(mySize[0]):
        myNorm = myNorm + t[i, :] ** 2
    return reshape(np.sqrt(myNorm), list(mySize[1:]))
