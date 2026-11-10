"""Port of src/mathOp/bmSquaredNorm.m."""

from monalisa.optim._euclidean_prod import euclidean_prod


def squared_norm(x, H):
    """Weighted squared norm ``real(x' * (H .* x))``."""
    return euclidean_prod(x, x, H)
