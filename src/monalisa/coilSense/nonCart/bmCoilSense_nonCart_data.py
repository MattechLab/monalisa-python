"""Port of src/coilSense/nonCart/bmCoilSense_nonCart_data.m."""

import numpy as np

from monalisa.arrayUtility.bmPermuteToCol import bmPermuteToCol
from monalisa.arrayUtility.bmPointReshape import bmPointReshape
from monalisa.geom123.bmVolumeElement import bmVolumeElement
from monalisa.mriRecon.function.bmLowRes import bmLowRes
from monalisa.trajN.bmTraj import bmTraj


def bmCoilSense_nonCart_data(reader, N_u, nargout=3):
    """Low-resolution data ``y`` (column format), trajectory ``t`` and volume
    elements ``ve`` of a raw file, restricted to the box of ``N_u`` points at
    the raw resolution ``1/FoV``. Returns up to ``nargout`` of ``(y, t, ve)``."""
    p = reader.acquisitionParams
    dK_u_raw = np.array([[1.0, 1.0, 1.0]]) / np.asarray(p.FoV, dtype=np.float64)
    y = reader.readRawData(True, True)
    t = bmPointReshape(bmTraj(p))
    if nargout in (1, 2):
        ve = np.ones((1, t.shape[1]))
    else:
        ve = bmVolumeElement(t, "voronoi_full_radial3")
    y, t, ve = bmLowRes(y, t, ve, N_u, dK_u_raw)
    y = bmPermuteToCol(y)
    return (y, t, ve)[0] if nargout <= 1 else (y, t, ve)[:nargout]
