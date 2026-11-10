"""Port of src/varargin/bmVarargin_sparseType.m."""

from monalisa._mat import isempty


def default_sparse_type(sparseType=None):
    """Default sparse type ``'SparseMat'``."""
    return "bmSparseMat" if isempty(sparseType) else sparseType
