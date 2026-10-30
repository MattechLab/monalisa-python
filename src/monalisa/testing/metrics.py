"""Image similarity metrics used to report MATLAB/Python agreement."""

from __future__ import annotations

import numpy as np


def rel_l2(x, ref) -> float:
    """Relative L2 error ``||x - ref|| / ||ref||``."""
    x = np.asarray(x, dtype=np.complex128).ravel()
    ref = np.asarray(ref, dtype=np.complex128).ravel()
    return float(np.linalg.norm(x - ref) / np.linalg.norm(ref))


def nmse(x, ref) -> float:
    """Normalized mean squared error ``||x - ref||^2 / ||ref||^2``."""
    return rel_l2(x, ref) ** 2


def ssim(x, ref) -> float:
    """Structural similarity of the magnitudes (mean over the slices of the last image
    axis for 3D volumes), with the data range of the reference."""
    from skimage.metrics import structural_similarity

    a = np.abs(np.asarray(x)).astype(np.float64)
    b = np.abs(np.asarray(ref)).astype(np.float64)
    rng = float(b.max() - b.min())
    if b.ndim == 2:
        return float(structural_similarity(a, b, data_range=rng))
    return float(np.mean([structural_similarity(a[..., k], b[..., k], data_range=rng)
                          for k in range(b.shape[-1])]))


def summary(x, ref) -> dict:
    return {"rel_l2": rel_l2(x, ref), "nmse": nmse(x, ref), "ssim": ssim(x, ref)}
