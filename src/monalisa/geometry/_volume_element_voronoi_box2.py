"""Port of src/geom2/bmVolumeElement_voronoi_box2.m."""

import numpy as np

from monalisa._mat import colon, vec
from monalisa.array._point_reshape import point_reshape
from monalisa.geometry._voronoi import voronoi


def volume_element_voronoi_box2(t, N_u, d_u):
    """Voronoi areas of 2D points bounded by a frame of extra points around the
    grid ``N_u`` with step ``d_u``."""
    N_u = vec(N_u)
    d_u = vec(d_u)
    t = np.asarray(point_reshape(t), dtype=np.float64)
    nPt = t.shape[1]
    Nx, Ny = N_u[0] + 1, N_u[1] + 1
    ys = colon(-(Ny / 2), Ny / 2 - 1)
    xs = colon(-(Nx / 2 - 1), Nx / 2 - 2)
    p1 = np.vstack([-(Nx / 2) * np.ones(int(Ny)) * d_u[0], ys * d_u[1]])
    p2 = np.vstack([(Nx / 2 - 1) * np.ones(int(Ny)) * d_u[0], ys * d_u[1]])
    p3 = np.vstack([xs * d_u[0], -(Ny / 2) * np.ones(int(Nx - 2)) * d_u[1]])
    p4 = np.vstack([xs * d_u[0], (Ny / 2 - 1) * np.ones(int(Nx - 2)) * d_u[1]])
    ve = voronoi(np.concatenate([t, p1, p2, p3, p4], axis=1))
    return ve[:, :nPt]
