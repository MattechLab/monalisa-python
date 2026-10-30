"""Port of src/traj123/bmTraj_lineDirection.m."""

import numpy as np

from monalisa._mat import msize, squeeze


def bmTraj_lineDirection(t):
    """Unit direction of each line of a trajectory in line format ``[imDim, N, nLine]``."""
    t = np.asarray(t)
    imDim, N, nLine = msize(t, 1), msize(t, 2), msize(t, 3)
    t = np.reshape(t, (imDim, N, nLine), order="F")
    e = t - t[:, 0:1, :]
    e = e[:, int(np.ceil(N / 2)) - 1 :, :]
    e_norm = np.zeros((1, e.shape[1], e.shape[2]), dtype=e.dtype)
    for i in range(imDim):
        e_norm = e_norm + e[i : i + 1, :, :] ** 2
    e = e / np.sqrt(e_norm)
    return squeeze(np.mean(e, axis=1, keepdims=True))
