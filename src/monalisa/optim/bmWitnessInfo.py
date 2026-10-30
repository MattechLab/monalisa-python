"""Port of src/optim/bmWitnessInfo.m (handle class)."""

from __future__ import annotations

import os

import numpy as np

from monalisa._mat import cell_items, iscell, isempty, msize, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.readWrite._mat73 import savemat73
from monalisa.time.bmTimeInSecond import bmTimeInSecond

_FIELDS = ("witness_name", "witness_ind", "save_witnessIm_flag", "witness_im", "witness_time",
           "creationTime", "finalCallTime", "finalInd", "param", "param_name")


def cell_set(lst: list, k: int, value) -> None:
    """MATLAB ``c{k} = value`` on a Python list (1-based, grows with ``None``)."""
    while len(lst) < k:
        lst.append(None)
    lst[k - 1] = value


def cell_row_set(lst: list, k: int, c: int, value) -> None:
    """MATLAB ``c{k}(1, c) = value`` (the row grows with zeros like MATLAB)."""
    current = lst[k - 1] if len(lst) >= k and lst[k - 1] is not None else np.zeros((1, 0))
    row = np.atleast_2d(np.asarray(current))
    if row.shape[1] < c:
        row = np.concatenate([row, np.zeros((row.shape[0], c - row.shape[1]), dtype=row.dtype)], axis=1)
    row = row.astype(np.result_type(row.dtype, np.asarray(value).dtype))
    row[0, c - 1] = value
    cell_set(lst, k, row)


class bmWitnessInfo:
    """Monitor of an iterative reconstruction: parameters, per-iteration values
    and, at the iterations ``witness_ind``, the current image saved to
    ``x_<name>.mat`` in ``out_dir`` (the working directory by default, like MATLAB)."""

    _matlab_handle = True

    def __init__(self, witness_name=None, witness_ind=None, save_witnessIm_flag=None):
        self.out_dir = os.getcwd()
        if isinstance(witness_name, bmWitnessInfo):
            for f in _FIELDS:
                setattr(self, f, getattr(witness_name, f))
            return
        self.witness_name = witness_name
        self.witness_ind = None if isempty(witness_ind) else vec(witness_ind)[None, :]
        self.save_witnessIm_flag = False if isempty(save_witnessIm_flag) else bool(save_witnessIm_flag)
        self.witness_im = None
        self.witness_time = None
        self.creationTime = bmTimeInSecond()
        self.finalCallTime = bmTimeInSecond()
        self.finalInd = None
        self.param = []
        self.param_name = []

    def watch(self, curr_ind, x, n_u, loop_or_final, z=None, u=None):
        """Record the iteration ``curr_ind``; save ``x`` (and ``z``, ``u``) when it is a witness index."""
        name = self.witness_name
        if isempty(self.witness_ind):
            return
        n_u = vec(n_u)
        if self.save_witnessIm_flag:
            im = bmBlockReshape(cell_items(x)[0] if iscell(x) else x, n_u)
            if n_u.size == 3:
                k = int(np.trunc(n_u[-1] / 2))
                im = np.concatenate([im[k, :, :], im[:, k, :], im[:, :, k]], axis=1)
            if n_u.size == 1:  # images side by side (MATLAB cat(2, ...))
                prev = self.witness_im
                self.witness_im = im if prev is None else np.concatenate([prev, im], axis=1)
            else:  # stacked along the 3rd dimension (MATLAB cat(3, ...))
                im = im[:, :, None]
                prev = self.witness_im
                self.witness_im = im if prev is None else np.concatenate(
                    [np.reshape(prev, (*im.shape[:2], -1), order="F"), im], axis=2)
        else:
            self.witness_im = None
        t = np.array([[bmTimeInSecond()]])
        self.witness_time = t if self.witness_time is None else np.concatenate([self.witness_time, t], axis=1)
        self.finalCallTime = bmTimeInSecond()
        self.finalInd = curr_ind
        if curr_ind in np.ravel(self.witness_ind):
            xs = {"x": bmBlockReshape(cell_items(x)[0], n_u) if iscell(x) else bmBlockReshape(x, n_u)}
            savemat73(os.path.join(self.out_dir, f"x_{name}.mat"), xs)
            if z is not None:
                savemat73(os.path.join(self.out_dir, f"z_{name}.mat"), {"z": z})
            if u is not None:
                savemat73(os.path.join(self.out_dir, f"u_{name}.mat"), {"u": u})
        if loop_or_final == "final":
            print(f"{name} completed. ")

    def parity_fields(self) -> dict:
        return {"witness_name": self.witness_name, "witness_ind": self.witness_ind}

    @classmethod
    def from_matlab_fields(cls, fields: dict) -> bmWitnessInfo:
        obj = cls.__new__(cls)
        obj.out_dir = os.getcwd()
        for f in _FIELDS:
            setattr(obj, f, fields.get(f))
        for f in ("param", "param_name"):
            v = getattr(obj, f)
            setattr(obj, f, [] if v is None else list(cell_items(v)) if iscell(v) else [v])
        flag = obj.save_witnessIm_flag
        obj.save_witnessIm_flag = False if flag is None else bool(np.ravel(flag)[0])
        if obj.witness_ind is not None and msize(obj.witness_ind) == (0, 0):
            obj.witness_ind = None
        return obj
