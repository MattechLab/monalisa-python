"""Minimal MATLAB v7.3 (HDF5) MAT-file reader and writer for numeric arrays.

Writes files that MATLAB ``load`` reads (512-byte userblock with the MAT
header, ``MATLAB_class`` attributes, dimensions reversed, complex as a
``real``/``imag`` compound) and reads numeric/logical arrays written by MATLAB.
"""

from __future__ import annotations

import datetime as dt
import os
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
    """Save numeric/logical arrays as a MATLAB v7.3 MAT-file (MATLAB shapes kept).

    The file is written next to ``path`` under a temporary name and renamed when complete, so that
    an interrupted run (killed kernel, full disk) never leaves a truncated file at ``path``."""
    path = Path(path)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        _write(tmp, variables)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def _write(path, variables: dict) -> None:
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


def _not_hdf5(path) -> Exception:
    """Error for a file that h5py cannot open: an older MAT-file, or an incomplete file."""
    size = os.path.getsize(path)
    with open(path, "rb") as fh:
        head = fh.read(128)
    if size == 0:
        why = "the file is empty"
    elif head.startswith(b"MATLAB") and not head.startswith(b"MATLAB 7.3"):
        return None  # a MAT-file of version 7 or older: read with scipy
    elif head.startswith(b"MATLAB 7.3"):
        why = f"the file is incomplete ({size} bytes): it was probably cut off while being written or copied"
    else:
        why = f"it is not a MAT-file ({size} bytes, starts with {head[:16]!r})"
    return OSError(f"loadmat73: cannot read {path}: {why}. Write it again (re-run the step that "
                   f"saves it), or copy it again completely.")


def loadmat73(path, variable_names=None) -> dict:
    """Numeric, logical and cell variables of a MATLAB v7.3 MAT-file, with MATLAB shapes.

    Older MAT-files (MATLAB ``save`` without ``-v7.3``) are read with ``scipy.io.loadmat``."""
    if not h5py.is_hdf5(path):
        err = _not_hdf5(path)
        if err is not None:
            raise err
        import scipy.io as sio

        data = sio.loadmat(path, variable_names=variable_names)
        return {k: v for k, v in data.items() if not k.startswith("__")}
    out = {}
    with h5py.File(path, "r") as f:
        for name, ds in f.items():
            if not isinstance(ds, h5py.Dataset) or name.startswith("#"):
                continue
            if variable_names is not None and name not in variable_names:
                continue
            out[name] = _read(f, ds)
    return out
