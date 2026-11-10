"""Demons registration (open-source replacement of MATLAB's imregdemons): behaviour without MATLAB."""

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter, map_coordinates

pytest.importorskip("SimpleITK")

from monalisa.registration._demons import _imresize, imregdemons  # noqa: E402
from monalisa.registration._im_deform_field_chain_im_reg_demons23 import im_deform_field_chain_im_reg_demons23  # noqa: E402
from monalisa.registration._im_deform_field_sheet_im_reg_demons23 import im_deform_field_sheet_im_reg_demons23  # noqa: E402


def _blobs(shape, seed=0):
    rng = np.random.default_rng(seed)
    im = gaussian_filter(rng.random(shape), 3)
    return 255 * (im - im.min()) / (im.max() - im.min())


def _warp(im, d):
    grid = np.meshgrid(*[np.arange(n, dtype=float) for n in im.shape], indexing="ij")
    return map_coordinates(im, [grid[k] + d[..., k] for k in range(im.ndim)], order=1, mode="nearest")


def _rel(a, b):
    return np.linalg.norm(a - b) / np.linalg.norm(b)


@pytest.mark.parametrize("shape", [(96, 80), (40, 36, 32)])
def test_demons_registers_smooth_deformation(shape):
    fixed = _blobs(shape)
    grid = np.meshgrid(*[np.arange(n, dtype=float) for n in shape], indexing="ij")
    d_true = np.stack([2.5 * np.sin(2 * np.pi * grid[(k + 1) % len(shape)] / shape[(k + 1) % len(shape)])
                       for k in range(len(shape))], axis=-1)
    moving = _warp(fixed, -d_true)  # moving(p) = fixed(p - d), so moving(p + d) ~ fixed(p)
    D, moving_reg = imregdemons(moving.astype(np.float32), fixed.astype(np.float32), [40, 20, 10])

    assert D.shape == shape + (len(shape),) and D.dtype == np.float64
    assert moving_reg.dtype == np.float32
    # away from the borders (zero outside the image, as MATLAB's imwarp with SmoothEdges)
    inner = tuple(slice(6, n - 6) for n in shape)
    assert _rel(moving_reg[inner], fixed[inner]) < 0.05 * _rel(moving[inner], fixed[inner])
    # MATLAB convention: D[..., 0] along x (axis 1), D[..., 1] along y (axis 0)
    d = D.copy()
    d[..., 0], d[..., 1] = D[..., 1], D[..., 0]
    epe = np.sqrt(((d - d_true) ** 2).sum(-1))[inner]
    assert epe.mean() < 0.4 * np.sqrt((d_true**2).sum(-1))[inner].mean()
    np.testing.assert_allclose(_warp(moving, d)[inner], moving_reg[inner], atol=1e-3 * 255,
                               err_msg="moving_reg is moving warped by D")


def test_demons_identity():
    im = _blobs((64, 64)).astype(np.float32)
    D, moving_reg = imregdemons(im, im, [10, 5, 2])
    assert np.abs(D).max() < 1e-6
    np.testing.assert_allclose(moving_reg, im, atol=1e-4)


def test_imresize_matlab_properties():
    a = np.random.default_rng(1).random((20, 14))
    assert _imresize(a, 0.5, "bicubic").shape == (10, 7)
    assert _imresize(a, 2.0, "bilinear").shape == (40, 28)
    np.testing.assert_allclose(_imresize(np.full((8, 6), 3.0), 0.5, "bicubic"), 3.0)
    # bilinear x2: output pixel i samples input (i + 1/2) / 2 - 1/2 (0-based), edges replicated
    np.testing.assert_allclose(_imresize(np.arange(4.0)[:, None] * np.ones((1, 2)), 2.0, "bilinear")[:, 0],
                               [0, 0.25, 0.75, 1.25, 1.75, 2.25, 2.75, 3])


def test_chain_wrapper_shapes():
    n_u = [48, 40]
    base = _blobs(n_u)
    grid = np.meshgrid(*[np.arange(n, dtype=float) for n in n_u], indexing="ij")
    x = np.empty((3, 1), dtype=object)
    for i in range(3):
        d = np.stack([1.5 * i * np.sin(np.pi * grid[1] / n_u[1]), np.zeros(n_u)], axis=-1)
        x[i, 0] = (_warp(base, d) * (1 + 0.5j)).astype(np.complex64)
    mask = np.zeros(n_u, bool)
    mask[4:-4, 4:-4] = True
    DF, im_out = im_deform_field_chain_im_reg_demons23(x, np.array([n_u], float), "curr_to_prev", 20, 1, None,
                                                       mask, 2, nargout=2)
    assert DF.shape == (3, 1) and im_out.shape == (3, 1)
    for v, im in zip(DF.flat, im_out.flat, strict=True):
        assert v.shape == (2, 48 * 40) and v.dtype == np.float64
        assert im.shape == tuple(n_u) and im.dtype == np.float32
        assert np.sqrt((v**2).sum(0)).max() <= 2 + 1e-9  # maxPixDisplacement
        assert not v[:, ~mask.ravel(order="F")].any()  # masked
    first = im_deform_field_chain_im_reg_demons23(x, n_u, "curr_to_first", 10, 1, None)
    assert first[0, 0] is None and first[1, 0].shape == (2, 48 * 40)


def test_sheet_wrapper_shapes():
    n_u = [32, 32]
    x = np.empty((2, 3), dtype=object)
    for k in range(6):
        x.flat[k] = _blobs(n_u, seed=k % 2).astype(np.float32)
    DF1, DF2, im1, im2 = im_deform_field_sheet_im_reg_demons23(x, n_u, "curr_to_next", [8, 8], 0, None, nargout=4)
    for c in (DF1, DF2, im1, im2):
        assert c.shape == (2, 3)
    assert DF1[0, 0].shape == (2, 32 * 32) and im2[1, 2].dtype == np.float32
