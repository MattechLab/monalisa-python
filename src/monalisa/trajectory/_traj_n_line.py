"""Port of src/traj123/bmTraj_nLine.m."""

import numpy as np

from monalisa.array._point_reshape import point_reshape


def _float_dtype(t):
    return t.dtype if t.dtype in (np.float32, np.float64) else np.float64


def traj_n_line(argTraj, nargout=1):
    """Detect the number of straight lines of a trajectory.

    Returns ``nLine`` or, for ``nargout > 1``, ``(nLine, N, isN_integer, dK_list)``
    truncated to ``nargout`` values, with ``N = nPt / nLine`` points per line.
    """
    t = np.asarray(point_reshape(argTraj))
    dt = _float_dtype(t)
    t = t.astype(dt, copy=False)
    th_n1 = 3.5
    th_n_de = 1 / 1000
    myEps = 10 * np.finfo(np.float64).eps
    delta_separation = myEps / (th_n_de / 1000)

    imDim, nPt = t.shape
    d1 = np.concatenate([np.zeros((imDim, 1), dtype=dt), t[:, 1:] - t[:, :-1]], axis=1)
    n1 = np.zeros(nPt, dtype=dt)
    for i in range(imDim):
        n1 = n1 + d1[i, :] ** 2
    n1 = np.sqrt(n1)
    n1[0] = 0

    jump_mask = n1 > th_n1 * np.median(n1)
    nonSeparated_mask = n1 <= delta_separation
    n1[nonSeparated_mask] = 1
    d1[:, nonSeparated_mask] = 0
    nonSeparated_mask = nonSeparated_mask | np.roll(nonSeparated_mask, -1)

    e = d1 / n1[None, :]
    de = e[:, 1:] - e[:, :-1]
    de[:, 0] = 0
    de = np.concatenate([de, np.zeros((imDim, 1), dtype=dt)], axis=1)
    n_de = np.zeros(nPt, dtype=dt)
    for i in range(imDim):
        n_de = n_de + de[i, :] ** 2
    n_de = np.sqrt(n_de)
    dirChange_mask = n_de > th_n_de

    outOfLine_mask = jump_mask | dirChange_mask | nonSeparated_mask
    inLine = ~outOfLine_mask[1:]
    previous = np.concatenate([[True], outOfLine_mask[1:-1]])
    nLine = float(np.sum(inLine & previous))
    dK_list = n1[1:][inLine][None, :]

    with np.errstate(divide="ignore", invalid="ignore"):
        N = np.float64(nPt) / np.float64(nLine)
        isN_integer = not (abs(N - np.round(N)) > 0)

    if nargout <= 1:
        return nLine
    return (nLine, N, isN_integer, dK_list)[:nargout]
