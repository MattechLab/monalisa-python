"""Minimal MATLAB v7.3 (HDF5) MAT-file reader and writer for numeric arrays.

Writes files that MATLAB ``load`` reads (512-byte userblock with the MAT
header, ``MATLAB_class`` attributes, dimensions reversed, complex as a
``real``/``imag`` compound) and reads numeric/logical arrays written by MATLAB.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import h5py
import numpy as np

_CLASS = {
    np.dtype(np.float64): "double", np.dtype(np.float32): "single",
    np.dtype(np.complex128): "double", np.dtype(np.complex64): "single",
    np.dtype(np.int8): "int8", np.dtype(np.int16): "int16", np.dtype(np.int32): "int32",
    np.dtype(np.int64): "int64", np.dtype(np.uint8): "uint8", np.dtype(np.uint16): "uint16",
    np.dtype(np.uint32): "uint32", np.dtype(np.uint64): "uint64", np.dtype(np.bool_): "logical",
}
_DTYPE = {"double": np.float64, "single": np.float32, "logical": np.bool_, "int8": np.int8,
          "int16": np.int16, "int32": np.int32, "int64": np.int64, "uint8": np.uint8,
          "uint16": np.uint16, "uint32": np.uint32, "uint64": np.uint64}


def _header() -> bytes:
    now = dt.datetime.now().strftime("%a %b %d %H:%M:%S %Y")
    text = f"MATLAB 7.3 MAT-file, Platform: GLNXA64, Created on: {now} HDF5 schema 1.00 ."
    return text.encode("ascii").ljust(116, b" ") + b"\x00" * 8 + b"\x00\x02" + b"IM"


def savemat73(path, variables: dict) -> None:
    """Save numeric/logical arrays as a MATLAB v7.3 MAT-file (MATLAB shapes kept)."""
    path = Path(path)
    with h5py.File(path, "w", userblock_size=512) as f:
        for name, value in variables.items():
            a = np.asarray(value)
            if a.ndim < 2:
                a = a.reshape(1, -1) if a.ndim == 1 else a.reshape(1, 1)
            cls = _CLASS[a.dtype]
            data = np.ascontiguousarray(a.T)  # HDF5 stores MATLAB arrays with reversed dims
            if np.iscomplexobj(a):
                comp = np.dtype([("real", data.real.dtype), ("imag", data.real.dtype)])
                buf = np.empty(data.shape, dtype=comp)
                buf["real"], buf["imag"] = data.real, data.imag
                data = buf
            elif cls == "logical":
                data = data.astype(np.uint8)
            ds = f.create_dataset(name, data=data)
            ds.attrs["MATLAB_class"] = np.bytes_(cls)
            if cls == "logical":
                ds.attrs["MATLAB_int_decode"] = np.int32(1)
    with open(path, "r+b") as fh:
        fh.write(_header())


def _read(f, ds):
    cls = ds.attrs.get("MATLAB_class", b"double")
    cls = cls.decode() if isinstance(cls, bytes) else str(cls)
    if "MATLAB_empty" in ds.attrs and ds.attrs["MATLAB_empty"]:
        return np.zeros((0, 0), dtype=_DTYPE.get(cls, np.float64))
    data = ds[()]
    if cls == "cell":
        refs = np.asarray(data).T
        out = np.empty(refs.shape, dtype=object)
        for idx in np.ndindex(refs.shape):
            out[idx] = _read(f, f[refs[idx]])
        return out
    if data.dtype.names and "real" in data.dtype.names:
        data = data["real"] + 1j * data["imag"]
    elif cls in _DTYPE:
        data = data.astype(_DTYPE[cls], copy=False)
    return np.asarray(data).T


def loadmat73(path, variable_names=None) -> dict:
    """Numeric, logical and cell variables of a MATLAB v7.3 MAT-file, with MATLAB shapes."""
    out = {}
    with h5py.File(path, "r") as f:
        for name, ds in f.items():
            if not isinstance(ds, h5py.Dataset) or name.startswith("#"):
                continue
            if variable_names is not None and name not in variable_names:
                continue
            out[name] = _read(f, ds)
    return out
