"""Port of src/arrayUtility/bmCol.m."""

from monalisa._mat import col


def bmCol(a):
    """MATLAB ``a(:)``."""
    return col(a)
