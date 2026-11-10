"""Port of src/trajN/bmTraj.m."""

from monalisa.trajectory._traj_full_radial3_phyllotaxis_line_assym2 import traj_full_radial3_phyllotaxis_line_assym2


def traj(mriAcquisition_node):
    """Trajectory of an acquisition, dispatched on ``mriAcquisition_node.traj_type``."""
    if not hasattr(mriAcquisition_node, "traj_type"):
        raise AttributeError("Missing required field: traj_type")
    traj_type = str(mriAcquisition_node.traj_type)
    if traj_type.lower() == "full_radial3_phylotaxis":
        return traj_full_radial3_phyllotaxis_line_assym2(mriAcquisition_node)
    if traj_type.lower() in ("uphy", "flexyphy", "pulseq"):
        raise NotImplementedError(f"traj: traj_type {traj_type!r} is not ported yet")
    raise ValueError(
        f'traj: Unknown traj_type "{traj_type}". This probably means your trajectory is not '
        "implemented. You need to implement it yourself."
    )
