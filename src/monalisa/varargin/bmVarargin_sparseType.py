"""Port of src/varargin/bmVarargin_sparseType.m."""

from monalisa._mat import isempty


def bmVarargin_sparseType(sparseType=None):
    """Default sparse type ``'bmSparseMat'``."""
    return "bmSparseMat" if isempty(sparseType) else sparseType
