"""Port of src/coilSense/automatic/detectROI.m."""

import numpy as np
from scipy import ndimage

from monalisa._mat import fix, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape


def _graythresh(img):
    """MATLAB ``graythresh``: Otsu threshold on a 256-bin histogram (``imhist``)."""
    num_bins = 256
    idx = np.floor(np.clip(np.ravel(img, order="F").astype(np.float64), 0, 1) * (num_bins - 1) + 0.5)
    counts = np.bincount(idx.astype(np.int64), minlength=num_bins).astype(np.float64)
    p = counts / counts.sum()
    omega = np.cumsum(p)
    mu = np.cumsum(p * np.arange(1, num_bins + 1))
    mu_t = mu[-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        sigma_b_squared = (mu_t * omega - mu) ** 2 / (omega * (1 - omega))
    maxval = np.nanmax(sigma_b_squared)
    if not np.isfinite(maxval):
        return 0.0
    k = np.mean(np.flatnonzero(sigma_b_squared == maxval) + 1)
    return (k - 1) / (num_bins - 1)


def _largest_bbox(binary):
    """``regionprops(bwconncomp(binary), 'BoundingBox', 'Area')`` of the largest
    8-connected component: ``[x, y, width, height]`` with x the column."""
    lab_t, n = ndimage.label(binary.T, structure=np.ones((3, 3), dtype=bool))  # MATLAB label order
    lab = lab_t.T
    areas = ndimage.sum_labels(np.ones_like(lab), lab, index=np.arange(1, n + 1))
    k = int(np.argmax(areas)) + 1
    rows, cols = np.nonzero(lab == k)
    width = cols.max() - cols.min() + 1
    height = rows.max() - rows.min() + 1
    return np.array([cols.min() + 0.5, rows.min() + 0.5, width, height], dtype=np.float64)


def _sum3(a):
    """MATLAB ``sum(a, 3)``: sequential accumulation over the third dimension."""
    s = np.zeros(a.shape[:2], dtype=a.dtype)
    for k in range(a.shape[2]):
        s = s + a[:, :, k]
    return s


def _normalize(a):
    return (a - a.min()) / (a.max() - a.min())


def detectROI(rawData, N_u):
    """Bounding box ``[xMin, xW; yMin, yW; zMin, zW]`` (1-based) of the object in a
    3D image, from Otsu-thresholded projections, padded by 3 voxels."""
    padding = 3
    N_u = vec(N_u)
    rawData = np.asarray(bmBlockReshape(rawData, N_u))
    zData = _normalize(_sum3(rawData))
    yData = _normalize(_sum3(np.transpose(rawData, (2, 0, 1))))
    xData = _normalize(_sum3(np.transpose(rawData, (1, 2, 0))))
    boxes = np.zeros((3, 4))
    for i, data in enumerate((xData, yData, zData)):
        boxes[i, :] = _largest_bbox(data > _graythresh(data))
    xMin = min(boxes[1, 0], boxes[2, 1])
    yMin = min(boxes[0, 1], boxes[2, 0])
    zMin = min(boxes[0, 0], boxes[1, 1])
    xW = max(boxes[1, 2], boxes[2, 3])
    yW = max(boxes[0, 3], boxes[2, 2])
    zW = max(boxes[0, 2], boxes[1, 3])
    xMin = max(fix(xMin - padding), 1)
    yMin = max(fix(yMin - padding), 1)
    zMin = max(fix(zMin - padding), 1)
    xW = min(fix(xW + 2 * padding), N_u[0] - xMin)
    yW = min(fix(yW + 2 * padding), N_u[1] - yMin)
    zW = min(fix(zW + 2 * padding), N_u[2] - zMin)
    return np.array([[xMin, xW], [yMin, yW], [zMin, zW]], dtype=np.float64)
