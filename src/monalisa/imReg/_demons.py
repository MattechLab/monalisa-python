"""Open-source replacement of MATLAB's ``imregdemons``, built on SimpleITK.

MATLAB's ``imregdemons`` (Image Processing Toolbox) is Thirion's demons
algorithm: at each iteration the update ``(F - M∘D) ∇F / (|∇F|² + (F - M∘D)²)``
(zero where ``|F - M∘D| < 0.001``, where the denominator is below ``1e-9`` or
where the warped moving image is outside its domain) is added to the
accumulated field, which is then smoothed with a Gaussian of standard deviation
``AccumulatedFieldSmoothing`` (1 pixel). It runs on a multiresolution pyramid
of ``numel(iterations)`` levels, coarsest first.

The iterations are done by ``itk::DemonsRegistrationFilter`` (SimpleITK), which
implements the same update with the same thresholds and the same field
regularization. The pyramid around it reproduces MATLAB's
(``MultiResolutionDemons2D/3D``): padding by replication to a multiple of
``2^(levels-1)``, images downsampled from full resolution at each level
(2D: antialiased bicubic ``imresize``; 3D: Butterworth low-pass and linear
resampling), field upsampled by 2 and multiplied by 2 between levels (2D:
bilinear ``imresize``; 3D: linear resampling). The remaining differences are
ITK's discrete Gaussian kernel and image gradient at the borders; the fields
agree in quality, not to rounding (docs/validation_registration.md).
"""

import numpy as np
from scipy.ndimage import map_coordinates

# truncation of ITK's Gaussian smoothing kernel (MATLAB samples the Gaussian on ceil(3 sigma))
_SMOOTHING_MAX_ERROR = 0.001


def _sitk():
    try:
        import SimpleITK as sitk
    except ImportError as e:  # pragma: no cover - depends on the environment
        raise ImportError("Demons registration requires SimpleITK: pip install 'monalisa[reg]'") from e
    return sitk


# --- MATLAB pyramid --------------------------------------------------------------------------

def _cubic(x):
    ax = np.abs(x)
    ax2, ax3 = ax**2, ax**3
    return ((1.5 * ax3 - 2.5 * ax2 + 1) * (ax <= 1)
            + (-0.5 * ax3 + 2.5 * ax2 - 4 * ax + 2) * ((ax > 1) & (ax <= 2)))


def _triangle(x):
    return (1 - np.abs(x)) * (np.abs(x) <= 1)


def _contributions(n_in, n_out, scale, kernel, kernel_width):
    """Weights and (0-based) indices of MATLAB's ``imresize`` along one dimension (antialiasing on)."""
    if scale < 1:
        h = lambda x: scale * kernel(scale * x)  # noqa: E731
        kernel_width = kernel_width / scale
    else:
        h = kernel
    x = np.arange(1, n_out + 1, dtype=np.float64)
    u = x / scale + 0.5 * (1 - 1 / scale)
    left = np.floor(u - kernel_width / 2)
    P = int(np.ceil(kernel_width)) + 2
    indices = left[:, None] + np.arange(P)[None, :]
    weights = h(u[:, None] - indices)
    weights = weights / weights.sum(axis=1, keepdims=True)
    aux = np.concatenate([np.arange(n_in), np.arange(n_in - 1, -1, -1)])
    indices = aux[np.mod(indices.astype(np.int64) - 1, aux.size)]
    keep = np.any(weights != 0, axis=0)
    return weights[:, keep], indices[:, keep]


def _imresize(a, scale, method):
    """MATLAB ``imresize(a, scale, method)`` of a 2D double image."""
    kernel, width = (_cubic, 4.0) if method == "bicubic" else (_triangle, 2.0)
    out = a
    for axis in range(2):
        n_in = out.shape[axis]
        n_out = int(np.ceil(n_in * scale))
        w, idx = _contributions(n_in, n_out, scale, kernel, width)
        moved = np.moveaxis(out, axis, 0)
        res = np.einsum("op,op...->o...", w, moved[idx])
        out = np.moveaxis(res, 0, axis)
    return out


def _normalized_frequency(n):
    if n % 2:
        return np.linspace(-0.5 + 1 / (2 * n), 0.5 - 1 / (2 * n), n)
    return np.linspace(-0.5, 0.5 - 1 / n, n)


def _antialias_resize3(a, factor):
    """``antialiasResize`` of MATLAB's ``MultiResolutionDemons3D``: Butterworth low-pass (order 2,
    cut-off ``factor/2``) if shrinking, then linear resampling by ``factor`` with smooth (zero) edges."""
    if factor == 1:
        return a
    if factor < 1:
        u, v, w = (_normalized_frequency(n) for n in a.shape)
        Dist = np.sqrt(u[:, None, None] ** 2 + v[None, :, None] ** 2 + w[None, None, :] ** 2)
        H = 1 / (1 + (Dist / (0.5 * factor)) ** 4)
        a = np.real(np.fft.ifftn(np.fft.ifftshift(np.fft.fftshift(np.fft.fftn(a)) * H)))
    n_out = [int(round(n * factor)) for n in a.shape]
    # output voxel j (1-based) <- input (j - 1/2) / factor + 1/2 (imwarp world limits [0.5, n + 0.5])
    coords = np.meshgrid(*[(np.arange(1, n + 1) - 0.5) / factor - 0.5 for n in n_out], indexing="ij")
    return map_coordinates(a, coords, order=1, mode="grid-constant", cval=0.0)


def _downsample(a, factor):
    if factor == 1:
        return a
    return _imresize(a, factor, "bicubic") if a.ndim == 2 else _antialias_resize3(a, factor)


def _upsample_field(d):
    """Accumulated field of the previous level -> next level (size x 2, displacements x 2)."""
    nd = d.shape[-1]
    if nd == 2:
        return np.stack([_imresize(d[..., k], 2.0, "bilinear") * 2 for k in range(nd)], axis=-1)
    return np.stack([_antialias_resize3(d[..., k], 2.0) * 2 for k in range(nd)], axis=-1)


# --- SimpleITK demons --------------------------------------------------------------------------

def _to_image(a):
    """numpy array (axis k = ITK dimension k), unit spacing -> SimpleITK image."""
    sitk = _sitk()
    return sitk.GetImageFromArray(np.ascontiguousarray(np.asarray(a, dtype=np.float64).T))


def _field_to_image(d):
    sitk = _sitk()
    nd = d.ndim - 1
    perm = tuple(range(nd))[::-1] + (nd,)
    return sitk.GetImageFromArray(np.ascontiguousarray(d.transpose(perm), dtype=np.float64), isVector=True)


def _field_from_image(img):
    sitk = _sitk()
    a = sitk.GetArrayFromImage(img)
    nd = a.ndim - 1
    return a.transpose(tuple(range(nd))[::-1] + (nd,))


def _demons_level(fixed, moving, d, nIter, sigma):
    """``nIter`` demons iterations on one pyramid level, starting from the field ``d`` (pixels, axis order)."""
    sitk = _sitk()
    nd = fixed.ndim
    demons = sitk.DemonsRegistrationFilter()
    demons.SetNumberOfIterations(nIter)
    demons.SetMaximumRMSError(0.0)  # MATLAB always runs all the iterations
    demons.SetIntensityDifferenceThreshold(0.001)
    demons.SetSmoothDisplacementField(True)
    demons.SetStandardDeviations([float(sigma)] * nd)
    demons.SetMaximumError(_SMOOTHING_MAX_ERROR)
    demons.SetSmoothUpdateField(False)
    demons.SetUseMovingImageGradient(False)
    field = demons.Execute(_to_image(fixed), _to_image(moving), _field_to_image(d))
    return _field_from_image(field)


def imregdemons(moving, fixed, iterations, accumulated_field_smoothing=1.0):
    """``[D, moving_reg] = imregdemons(moving, fixed, iterations)`` with ``numel(iterations)`` levels.

    MATLAB conventions: ``D[..., 0]`` is the displacement along x (columns,
    axis 1), ``D[..., 1]`` along y (rows, axis 0), ``D[..., 2]`` along z, in
    pixels; ``moving_reg(p) = moving(p + D(p))`` (linear interpolation, zero
    outside). ``D`` is double, ``moving_reg`` has the class of ``moving``.
    """
    moving = np.asarray(moving)
    fixed_a = np.asarray(fixed, dtype=np.float64)
    moving_a = moving.astype(np.float64)
    if fixed_a.shape != moving_a.shape or fixed_a.ndim not in (2, 3):
        raise ValueError("imregdemons: moving and fixed must be 2D or 3D images of the same size")
    iterations = [int(n) for n in np.ravel(iterations)]
    nLevel = len(iterations)
    shape0 = fixed_a.shape
    nd = fixed_a.ndim

    div = 2 ** (nLevel - 1)
    pad = [(0, (-n) % div) for n in shape0]
    fixed_a = np.pad(fixed_a, pad, mode="edge")
    moving_a = np.pad(moving_a, pad, mode="edge")

    d = None
    for level, nIter in enumerate(iterations):
        factor = 0.5 ** (nLevel - 1 - level)
        fixed_l = _downsample(fixed_a, factor)
        moving_l = _downsample(moving_a, factor)
        d = np.zeros(fixed_l.shape + (nd,)) if d is None else _upsample_field(d)
        if nIter > 0:
            d = _demons_level(fixed_l, moving_l, d, nIter, accumulated_field_smoothing)

    d = d[tuple(slice(0, n) for n in shape0)]
    D = d.copy()
    D[..., 0], D[..., 1] = d[..., 1], d[..., 0]

    grid = np.meshgrid(*[np.arange(n, dtype=np.float64) for n in shape0], indexing="ij")
    coords = [grid[k] + d[..., k] for k in range(nd)]
    moving_reg = map_coordinates(moving.astype(np.float64), coords, order=1, mode="grid-constant", cval=0.0)
    return D, moving_reg.astype(moving.dtype if np.issubdtype(moving.dtype, np.floating) else np.float64)
