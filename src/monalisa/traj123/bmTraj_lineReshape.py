"""Port of src/traj123/bmTraj_lineReshape.m."""

from monalisa._mat import msize, reshape
from monalisa.traj123.bmTraj_nLine import bmTraj_nLine


def bmTraj_lineReshape(t, data=None, nargout=1):
    """Reshape a trajectory (and optionally its data) to line format ``[imDim, N, nLine]``."""
    imDim = msize(t, 1)
    nLine, N, isN_integer = bmTraj_nLine(t, nargout=3)
    if not isN_integer:
        raise ValueError("The size of traj is not convertible to [imDim, N, nLine]")
    out = reshape(t, [imDim, N, nLine])
    if nargout <= 1:
        return out
    if data is None:
        raise ValueError("bmTraj_lineReshape: data is required for a second output")
    return out, reshape(data, [msize(data, 1), N, nLine])
