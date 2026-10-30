"""Port of src/geom123/bmVolumeElement.m."""

import warnings

import numpy as np

from monalisa._mat import cell_from_items, cell_items, cell_shape, iscell
from monalisa.arrayUtility.bmPointReshape import bmPointReshape
from monalisa.geom2.bmVolumeElement_cartesian2 import bmVolumeElement_cartesian2
from monalisa.geom2.bmVolumeElement_randomPartialCartesian2_x import bmVolumeElement_randomPartialCartesian2_x
from monalisa.geom2.bmVolumeElement_voronoi_box2 import bmVolumeElement_voronoi_box2
from monalisa.geom2.bmVolumeElement_voronoi_center_out_radial2 import (
    bmVolumeElement_voronoi_center_out_radial2,
)
from monalisa.geom2.bmVolumeElement_voronoi_full_radial2 import bmVolumeElement_voronoi_full_radial2
from monalisa.geom3.bmVolumeElement_center_out_radial3 import bmVolumeElement_center_out_radial3
from monalisa.geom3.bmVolumeElement_full_radial3 import bmVolumeElement_full_radial3
from monalisa.geom3.bmVolumeElement_randomPartialCartesian3_x import bmVolumeElement_randomPartialCartesian3_x
from monalisa.geom3.bmVolumeElement_voronoi_full_radial3 import bmVolumeElement_voronoi_full_radial3
from monalisa.traj123.bmTraj_formatTraj import bmTraj_formatTraj


def _formatted(func):
    """Types computed on the trajectory with merged center points (``bmTraj_formatTraj``)."""

    def ve(t, N_u, dK_u):
        formatedTraj, _, formatedIndex, formatedWeight = bmTraj_formatTraj(t, nargout=4)
        v = np.ravel(func(formatedTraj, N_u, dK_u), order="F")
        return (v[np.ravel(formatedIndex).astype(np.int64) - 1] * np.ravel(formatedWeight))[None, :]

    return ve


_PORTED = {
    "voronoi_box2": _formatted(bmVolumeElement_voronoi_box2),
    "voronoi_center_out_radial2": lambda t, N_u, dK_u: bmVolumeElement_voronoi_center_out_radial2(t),
    "voronoi_full_radial2": lambda t, N_u, dK_u: bmVolumeElement_voronoi_full_radial2(t),
    "voronoi_full_radial3": lambda t, N_u, dK_u: bmVolumeElement_voronoi_full_radial3(t),
    "cartesian2": lambda t, N_u, dK_u: bmVolumeElement_cartesian2(t),
    "randomPartialCartesian2_x": bmVolumeElement_randomPartialCartesian2_x,
    "randomPartialCartesian3_x": bmVolumeElement_randomPartialCartesian3_x,
    "full_radial3": lambda t, N_u, dK_u: bmVolumeElement_full_radial3(t),
    "center_out_radial3": lambda t, N_u, dK_u: bmVolumeElement_center_out_radial3(t),
}

_KNOWN = {
    "voronoi_box3", "voronoi_center_out_radial3", "voronoi_full_radial2_nonUnique",
    "voronoi_full_radial3_nonUnique", "imDeformField2", "imDeformField3", "cartesian3",
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
        v = _PORTED[argType](t, N_u, dK_u)
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
