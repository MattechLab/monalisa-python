"""Port of src/trajN/bmTraj.m."""

from monalisa.traj3.bmTraj_fullRadial3_phyllotaxis_lineAssym2 import bmTraj_fullRadial3_phyllotaxis_lineAssym2


def bmTraj(mriAcquisition_node):
    """Trajectory of an acquisition, dispatched on ``mriAcquisition_node.traj_type``."""
    if not hasattr(mriAcquisition_node, "traj_type"):
        raise AttributeError("Missing required field: traj_type")
    traj_type = str(mriAcquisition_node.traj_type)
    if traj_type.lower() == "full_radial3_phylotaxis":
        return bmTraj_fullRadial3_phyllotaxis_lineAssym2(mriAcquisition_node)
    if traj_type.lower() in ("uphy", "flexyphy", "pulseq"):
        raise NotImplementedError(f"bmTraj: traj_type {traj_type!r} is not ported yet")
    raise ValueError(
        f'bmTraj: Unknown traj_type "{traj_type}". This probably means your trajectory is not '
        "implemented. You need to implement it yourself."
    )
