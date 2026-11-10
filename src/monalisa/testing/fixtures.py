"""Loading of MATLAB golden recordings and conversion to Python conventions."""

from __future__ import annotations

import warnings
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import scipy.io as sio
from scipy.io.matlab import mat_struct

from monalisa._mat import Struct

# Converters for recorded MATLAB objects, keyed by MATLAB class name.
OBJECT_CONVERTERS: dict = {}


def register_object_converter(matlab_class: str):
    def deco(fn):
        OBJECT_CONVERTERS[matlab_class] = fn
        return fn

    return deco


@dataclass
class Record:
    func: str
    scenario: str
    path: Path
    nargin: int
    nargout: int
    caller: str
    upstream: str
    inputs: list = field(repr=False)
    outputs: list = field(repr=False)

    @property
    def id(self) -> str:
        return f"{self.scenario}/{self.func}/{self.path.stem}"


def _str(x) -> str:
    x = np.asarray(x)
    return str(x.item()) if x.size else ""


def _cell_list(c) -> list:
    if isinstance(c, np.ndarray) and c.dtype == object:
        return list(c.ravel(order="F"))
    if isinstance(c, np.ndarray) and c.size == 0:
        return []
    return [c]


def _merge_class(stored, typed):
    """Combine two loadmat results of the same file.

    ``mat_dtype=True`` restores the MATLAB class of arrays that MATLAB saved in
    a smaller integer type, but scipy then drops the imaginary part of complex
    arrays; ``mat_dtype=False`` keeps complex values. Values are taken from
    ``stored`` and the precision from ``typed``.
    """
    if isinstance(stored, mat_struct):
        for f in stored._fieldnames:
            setattr(stored, f, _merge_class(getattr(stored, f), getattr(typed, f)))
        return stored
    if isinstance(stored, np.ndarray):
        if stored.dtype == object:
            for idx in np.ndindex(stored.shape):
                stored[idx] = _merge_class(stored[idx], typed[idx])
            return stored
        if np.iscomplexobj(stored):
            single = typed.dtype in (np.float32, np.complex64)
            return stored.astype(np.complex64 if single else np.complex128)
        return typed
    return typed


def load_record(path) -> Record:
    path = Path(path)
    opts = dict(squeeze_me=False, struct_as_record=False, chars_as_strings=True)
    stored = sio.loadmat(path, mat_dtype=False, **opts)["rec"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", np.exceptions.ComplexWarning)
        typed = sio.loadmat(path, mat_dtype=True, **opts)["rec"]
    raw = _merge_class(stored, typed)[0, 0]
    return Record(
        func=_str(raw.func),
        scenario=_str(raw.scenario),
        path=path,
        nargin=int(np.asarray(raw.nargin).item()),
        nargout=int(np.asarray(raw.nargout).item()),
        caller=_str(raw.caller),
        upstream=_str(raw.upstream),
        inputs=_cell_list(raw.inputs),
        outputs=_cell_list(raw.outputs),
    )


def iter_records(root, funcs=None) -> Iterator[Path]:
    """Yield record paths below ``root`` (optionally only for ``funcs``)."""
    root = Path(root)
    if not root.exists():
        return
    for p in sorted(root.glob("*/*/call_*.mat")):
        if funcs is None or p.parent.name in funcs:
            yield p


def from_matlab(x, role: str = "input"):
    """Convert loaded MATLAB data to the conventions of the Python port.

    For ``role="input"``: ``[]`` (0x0 double) becomes ``None`` and 1x1
    numeric arrays become numpy scalars of the same dtype. Outputs keep
    their array form so that shapes can be compared.
    """
    if isinstance(x, mat_struct):
        fields = {f: from_matlab(getattr(x, f), role) for f in x._fieldnames}
        cls = fields.pop("matlabClass", None)
        if cls is None:  # recordings made before the capture tools were renamed
            cls = fields.pop("mlpClass", None)
        if cls is not None:
            conv = OBJECT_CONVERTERS.get(cls)
            if conv is None:
                import monalisa

                ported = monalisa.find_function(cls)
                conv = getattr(ported, "from_matlab_fields", None)
            if conv is not None:
                return conv(fields)
            s = Struct(fields)
            s["_class"] = cls
            return s
        return Struct(fields)
    if isinstance(x, np.ndarray):
        if x.dtype == object:
            if x.size == 1 and isinstance(x.flat[0], mat_struct):
                return from_matlab(x.flat[0], role)
            out = np.empty(x.shape, dtype=object)
            for idx in np.ndindex(x.shape):
                out[idx] = from_matlab(x[idx], role)
            return out
        if x.dtype.kind == "U":
            return str(x.item()) if x.size else ""
        if role == "input":
            if x.shape == (0, 0) and x.dtype == np.float64:
                return None
            if x.size == 1 and x.ndim == 2:
                return x.dtype.type(x.item())
        return x
    return x
