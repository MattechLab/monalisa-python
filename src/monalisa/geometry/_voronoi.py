"""Port of src/geom123/bmVoronoi.m (MATLAB voronoin/convhulln -> scipy Qhull)."""

import numba
import numpy as np
from scipy.spatial import ConvexHull, QhullError, Voronoi

from monalisa._mat import disp, double
from monalisa.geometry._volume_element1 import volume_element1


@numba.njit(cache=True)
def _polygon_areas(vertices, flat, ptr, out):
    """Area of the convex polygons ``vertices[flat[ptr[k]:ptr[k+1]]]`` (shoelace
    after sorting the vertices by angle around their centroid). Degenerate
    polygons get -1, like a failing ``convhulln``."""
    for k in range(ptr.size - 1):
        idx = flat[ptr[k] : ptr[k + 1]]
        n = idx.size
        if n < 3:
            out[k] = -1.0
            continue
        cx = 0.0
        cy = 0.0
        for i in range(n):
            cx += vertices[idx[i], 0]
            cy += vertices[idx[i], 1]
        cx /= n
        cy /= n
        ang = np.empty(n)
        for i in range(n):
            ang[i] = np.arctan2(vertices[idx[i], 1] - cy, vertices[idx[i], 0] - cx)
        order = np.argsort(ang)
        area = 0.0
        for i in range(n):
            a = idx[order[i]]
            b = idx[order[(i + 1) % n]]
            area += vertices[a, 0] * vertices[b, 1] - vertices[b, 0] * vertices[a, 1]
        area = 0.5 * abs(area)
        out[k] = area if area > 0.0 else -1.0


def voronoi(x, dispFlag=True):
    """Voronoi cell volume of each point of ``x`` (``[imDim, nPt]``).

    Unbounded cells get -1. For ``imDim == 1`` the 1D lengths of
    ``volume_element1`` are returned (as a column, like MATLAB).
    """
    x = double(x)
    imDim, nPt = x.shape
    if imDim == 1:
        return volume_element1(x)
    if imDim not in (2, 3):
        raise ValueError("voronoi: only 1, 2 or 3 dimensions are supported")
    if dispFlag:
        disp("Running 'voronoin' and 'convhulln'... can take some time ...")

    vor = Voronoi(x.T, qhull_options="Qbb")
    regions = [vor.regions[r] if r >= 0 else [-1] for r in vor.point_region]
    bounded = np.array([len(r) > 0 and -1 not in r for r in regions])
    out = -np.ones((1, nPt))

    if imDim == 2:
        sel = np.flatnonzero(bounded)
        lens = np.array([len(regions[j]) for j in sel], dtype=np.int64)
        ptr = np.concatenate([[0], np.cumsum(lens)]).astype(np.int64)
        flat = np.fromiter(
            (v for j in sel for v in regions[j]), dtype=np.int64, count=int(ptr[-1])
        )
        areas = np.empty(sel.size)
        _polygon_areas(vor.vertices, flat, ptr, areas)
        out[0, sel] = areas
    else:
        for j in np.flatnonzero(bounded):
            try:
                out[0, j] = ConvexHull(vor.vertices[regions[j]]).volume
            except QhullError:
                out[0, j] = -1.0

    if dispFlag:
        disp("... 'voronoin' and 'convhulln' done !")
    return out
