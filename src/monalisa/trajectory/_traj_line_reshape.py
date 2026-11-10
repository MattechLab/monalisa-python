"""Port of src/traj123/bmTraj_lineReshape.m."""

from monalisa._mat import msize, reshape
from monalisa.trajectory._traj_n_line import traj_n_line


def traj_line_reshape(t, data=None, nargout=1):
    """Reshape a trajectory (and optionally its data) to line format ``[imDim, N, nLine]``."""
    imDim = msize(t, 1)
    nLine, N, isN_integer = traj_n_line(t, nargout=3)
    if not isN_integer:
        raise ValueError("The size of traj is not convertible to [imDim, N, nLine]")
    out = reshape(t, [imDim, N, nLine])
    if nargout <= 1:
        return out
    if data is None:
        raise ValueError("traj_line_reshape: data is required for a second output")
    return out, reshape(data, [msize(data, 1), N, nLine])
