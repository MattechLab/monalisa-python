"""Port of src/coilSense/nonCart/bmCoilSense_nonCart_data.m."""

import numpy as np

from monalisa.array._permute_to_col import permute_to_col
from monalisa.array._point_reshape import point_reshape
from monalisa.geometry._volume_element import volume_element
from monalisa.trajectory._low_res import low_res
from monalisa.trajectory._traj import traj


def coil_sense_non_cart_data(reader, N_u, nargout=3):
    """Low-resolution data ``y`` (column format), trajectory ``t`` and volume
    elements ``ve`` of a raw file, restricted to the box of ``N_u`` points at
    the raw resolution ``1/FoV``. Returns up to ``nargout`` of ``(y, t, ve)``."""
    p = reader.acquisitionParams
    dK_u_raw = np.array([[1.0, 1.0, 1.0]]) / np.asarray(p.FoV, dtype=np.float64)
    y = reader.read_raw_data(True, True)
    t = point_reshape(traj(p))
    if nargout in (1, 2):
        ve = np.ones((1, t.shape[1]))
    else:
        ve = volume_element(t, "voronoi_full_radial3")
    y, t, ve = low_res(y, t, ve, N_u, dK_u_raw)
    y = permute_to_col(y)
    return (y, t, ve)[0] if nargout <= 1 else (y, t, ve)[:nargout]
