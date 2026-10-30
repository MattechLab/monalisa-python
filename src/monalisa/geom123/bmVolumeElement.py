"""Port of src/geom123/bmVolumeElement.m."""

import warnings

import numpy as np

from monalisa._mat import cell_from_items, cell_items, cell_shape, iscell
from monalisa.arrayUtility.bmPointReshape import bmPointReshape
from monalisa.geom2.bmVolumeElement_voronoi_full_radial2 import bmVolumeElement_voronoi_full_radial2
from monalisa.geom3.bmVolumeElement_voronoi_full_radial3 import bmVolumeElement_voronoi_full_radial3

_PORTED = {
    "voronoi_full_radial2": bmVolumeElement_voronoi_full_radial2,
    "voronoi_full_radial3": bmVolumeElement_voronoi_full_radial3,
}

_KNOWN = {
    "voronoi_box2", "voronoi_box3", "voronoi_center_out_radial2", "voronoi_center_out_radial3",
    "voronoi_full_radial2_nonUnique", "voronoi_full_radial3_nonUnique", "imDeformField2",
    "imDeformField3", "cartesian2", "cartesian3", "randomPartialCartesian2_x",
    "randomPartialCartesian3_x", "full_radial3", "center_out_radial3",
}


def bmVolumeElement(argTraj, argType, *varargin):
    """Volume elements (density compensation) of a trajectory, or of each
    trajectory of a cell. ``varargin`` is ``(N_u, dK_u)`` as in MATLAB."""
    N_u = varargin[0] if len(varargin) > 0 else None
    dK_u = varargin[1] if len(varargin) > 1 else None
    if iscell(argTraj):
        return cell_from_items(
            [bmVolumeElement(a, argType, N_u, dK_u) for a in cell_items(argTraj)], cell_shape(argTraj)
        )
    t = bmPointReshape(argTraj)
    if argType in _PORTED:
        v = _PORTED[argType](t)
    elif argType in _KNOWN:
        raise NotImplementedError(f"bmVolumeElement type '{argType}' is not ported yet")
    else:
        raise ValueError(
            "Trajectory type is unknown: check the possible inputs, or implement you new "
            "custom Volume Element function"
        )
    if np.sum(np.isnan(v)) > 0:
        warnings.warn("There is some NaNs in the volume elements !!! You need to replace it. ", stacklevel=2)
    return v
