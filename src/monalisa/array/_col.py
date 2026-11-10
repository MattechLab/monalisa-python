"""Port of src/arrayUtility/bmCol.m."""

from monalisa import _mat


def col(a):
    """MATLAB ``a(:)``."""
    return _mat.col(a)
