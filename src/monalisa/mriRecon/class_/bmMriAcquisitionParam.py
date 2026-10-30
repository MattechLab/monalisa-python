"""Port of src/mriRecon/class/bmMriAcquisitionParam.m (handle class)."""

from __future__ import annotations

import numpy as np

from monalisa._mat import isempty

_DEFAULTS = {
    "class_type": "bmMriAcquisitionParam",
    "node_type": "mriAcquisition_node",
    "name": "void",
    "mainFile_name": "void",
    "pulseqTrajFile_name": "void",
    "imDim": None,
    "N": None,
    "nSeg": None,
    "nShot": None,
    "nPar": None,
    "nLine": None,
    "nPt": None,
    "nCh": None,
    "nEcho": None,
    "raw_N_u": None,
    "raw_dK_u": None,
    "selfNav_flag": None,
    "nShot_off": None,
    "roosk_flag": None,
    "FoV": None,
    "timestamp": None,
    "traj_type": "void",
    "check_flag": True,
}


class bmMriAcquisitionParam:
    """Acquisition parameters of a raw data set (number of points per line ``N``,
    segments ``nSeg``, shots ``nShot``, ``FoV``, trajectory type, ...)."""

    def __init__(self, arg_name=None):
        for k, v in _DEFAULTS.items():
            setattr(self, k, v)
        self.name = arg_name

    def refresh(self):
        """Fill the missing counts from the others (as single, like MATLAB)."""
        if isempty(self.N):
            self.N = np.float32(self.nPt / self.nLine)
        if isempty(self.nSeg):
            self.nSeg = np.float32(self.nLine / self.nShot)
        if isempty(self.nShot):
            self.nShot = np.float32(self.nLine / self.nSeg)
        if isempty(self.nLine):
            self.nLine = np.float32(self.nSeg * self.nShot)
        if isempty(self.nPt):
            self.nPt = np.float32(self.N * self.nSeg * self.nShot)

    def parity_fields(self) -> dict:
        return {k: getattr(self, k) for k in _DEFAULTS}

    @classmethod
    def from_matlab_fields(cls, fields: dict) -> bmMriAcquisitionParam:
        obj = cls()
        for k in _DEFAULTS:
            if k in fields:
                val = fields[k]
                if isinstance(val, np.ndarray) and val.size == 0:
                    val = None
                setattr(obj, k, val)
        for k, v in fields.items():
            if k not in _DEFAULTS:
                setattr(obj, k, v)
        return obj

    def __repr__(self):
        return (f"bmMriAcquisitionParam(N={self.N}, nSeg={self.nSeg}, nShot={self.nShot}, "
                f"nShot_off={self.nShot_off}, FoV={self.FoV}, traj_type={self.traj_type!r})")
