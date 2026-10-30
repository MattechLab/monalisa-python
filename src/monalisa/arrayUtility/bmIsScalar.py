"""Port of src/arrayUtility/bmIsScalar.m."""

from monalisa._mat import iscell, numel


def bmIsScalar(x):
    """True for a single element that is not a cell."""
    return (not iscell(x)) and numel(x) == 1
