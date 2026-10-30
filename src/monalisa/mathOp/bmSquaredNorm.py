"""Port of src/mathOp/bmSquaredNorm.m."""

from monalisa.mathOp.bmEuclideProd import bmEuclideProd


def bmSquaredNorm(x, H):
    """Weighted squared norm ``real(x' * (H .* x))``."""
    return bmEuclideProd(x, x, H)
