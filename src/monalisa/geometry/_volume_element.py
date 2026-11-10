"""Port of src/geom123/bmVolumeElement.m."""

import warnings

import numpy as np

from monalisa._mat import cell_from_items, cell_items, cell_shape, iscell
from monalisa.array._point_reshape import point_reshape
from monalisa.geometry._volume_element_cartesian2 import volume_element_cartesian2
from monalisa.geometry._volume_element_center_out_radial3 import volume_element_center_out_radial3
from monalisa.geometry._volume_element_full_radial3 import volume_element_full_radial3
from monalisa.geometry._volume_element_random_partial_cartesian2_x import volume_element_random_partial_cartesian2_x
from monalisa.geometry._volume_element_random_partial_cartesian3_x import volume_element_random_partial_cartesian3_x
from monalisa.geometry._volume_element_voronoi_box2 import volume_element_voronoi_box2
from monalisa.geometry._volume_element_voronoi_center_out_radial2 import volume_element_voronoi_center_out_radial2
from monalisa.geometry._volume_element_voronoi_full_radial2 import volume_element_voronoi_full_radial2
from monalisa.geometry._volume_element_voronoi_full_radial3 import volume_element_voronoi_full_radial3
from monalisa.trajectory._traj_format import traj_format


def _formatted(func):
    """Types computed on the trajectory with merged center points (``traj_format``)."""

    def ve(t, N_u, dK_u):
        formatedTraj, _, formatedIndex, formatedWeight = traj_format(t, nargout=4)
        v = np.ravel(func(formatedTraj, N_u, dK_u), order="F")
        return (v[np.ravel(formatedIndex).astype(np.int64) - 1] * np.ravel(formatedWeight))[None, :]

    return ve


_PORTED = {
    "voronoi_box2": _formatted(volume_element_voronoi_box2),
    "voronoi_center_out_radial2": lambda t, N_u, dK_u: volume_element_voronoi_center_out_radial2(t),
    "voronoi_full_radial2": lambda t, N_u, dK_u: volume_element_voronoi_full_radial2(t),
    "voronoi_full_radial3": lambda t, N_u, dK_u: volume_element_voronoi_full_radial3(t),
    "cartesian2": lambda t, N_u, dK_u: volume_element_cartesian2(t),
    "randomPartialCartesian2_x": volume_element_random_partial_cartesian2_x,
    "randomPartialCartesian3_x": volume_element_random_partial_cartesian3_x,
    "full_radial3": lambda t, N_u, dK_u: volume_element_full_radial3(t),
    "center_out_radial3": lambda t, N_u, dK_u: volume_element_center_out_radial3(t),
}

_KNOWN = {
    "voronoi_box3", "voronoi_center_out_radial3", "voronoi_full_radial2_nonUnique",
    "voronoi_full_radial3_nonUnique", "imDeformField2", "imDeformField3", "cartesian3",
}


def volume_element(argTraj, argType, *varargin):
    """Volume elements (density compensation) of a trajectory, or of each
    trajectory of a cell. ``varargin`` is ``(N_u, dK_u)`` as in MATLAB."""
    N_u = varargin[0] if len(varargin) > 0 else None
    dK_u = varargin[1] if len(varargin) > 1 else None
    if iscell(argTraj):
        return cell_from_items(
            [volume_element(a, argType, N_u, dK_u) for a in cell_items(argTraj)], cell_shape(argTraj)
        )
    t = point_reshape(argTraj)
    if argType in _PORTED:
        v = _PORTED[argType](t, N_u, dK_u)
    elif argType in _KNOWN:
        raise NotImplementedError(f"volume_element type '{argType}' is not ported yet")
    else:
        raise ValueError(
            "Trajectory type is unknown: check the possible inputs, or implement you new "
            "custom Volume Element function"
        )
    if np.sum(np.isnan(v)) > 0:
        warnings.warn("There is some NaNs in the volume elements !!! You need to replace it. ", stacklevel=2)
    return v
