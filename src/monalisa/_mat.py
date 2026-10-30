"""Helpers reproducing MATLAB semantics used throughout the faithful port.

Conventions (see CONVENTIONS.md):

* arrays keep MATLAB shapes and are reshaped in Fortran (column-major) order;
* MATLAB ``[]`` passed as an argument is ``None``;
* cell arrays are object ndarrays with the MATLAB shape (lists are accepted
  as input and treated as column cells);
* MATLAB ``single`` is float32/complex64, ``double`` is float64/complex128.
"""

from __future__ import annotations

import numpy as np


class Struct(dict):
    """MATLAB struct: a dict with attribute access."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        del self[name]


def isempty(x) -> bool:
    """MATLAB ``isempty``; ``None`` is the Python stand-in for ``[]``."""
    if x is None:
        return True
    if isinstance(x, (str, list, tuple)):
        return len(x) == 0
    return np.size(x) == 0


def iscell(x) -> bool:
    return isinstance(x, (list, tuple)) or (isinstance(x, np.ndarray) and x.dtype == object)


def cell_shape(c) -> tuple:
    """MATLAB size of a cell (lists are column cells)."""
    if isinstance(c, (list, tuple)):
        return (len(c), 1)
    return msize(c)


def cell_items(c) -> list:
    """Elements of a cell in MATLAB linear (column-major) order."""
    if isinstance(c, (list, tuple)):
        return list(c)
    return list(c.ravel(order="F"))


def new_cell(shape) -> np.ndarray:
    return np.empty(tuple(int(s) for s in shape), dtype=object)


def cell_from_items(items, shape) -> np.ndarray:
    """Build a cell of MATLAB size ``shape`` from items in linear order."""
    flat = np.empty(len(items), dtype=object)
    for i, item in enumerate(items):
        flat[i] = item
    return flat.reshape(tuple(int(s) for s in shape), order="F")


def msize(x, dim=None):
    """MATLAB ``size``: at least 2 dims, trailing singletons beyond 2 dropped.

    ``dim`` is 1-based like in MATLAB.
    """
    if isinstance(x, (list, tuple)):
        shape = (len(x), 1)
    else:
        shape = np.shape(x)
    shape = tuple(int(s) for s in shape)
    if len(shape) == 0:
        shape = (1, 1)
    elif len(shape) == 1:
        shape = (shape[0], 1)
    while len(shape) > 2 and shape[-1] == 1:
        shape = shape[:-1]
    if dim is None:
        return shape
    return shape[dim - 1] if dim <= len(shape) else 1


def ndims(x) -> int:
    return len(msize(x))


def numel(x) -> int:
    if isinstance(x, (list, tuple)):
        return len(x)
    return int(np.size(x))


def col(x) -> np.ndarray:
    """MATLAB ``x(:)``."""
    return np.reshape(np.asarray(x), (-1, 1), order="F")


def row(x) -> np.ndarray:
    """MATLAB ``x(:).'``."""
    return np.reshape(np.asarray(x), (1, -1), order="F")


def reshape(x, *shape) -> np.ndarray:
    """MATLAB ``reshape`` (column-major), shape given as list or arguments."""
    if len(shape) == 1:
        shape = shape[0]
    dims = [int(s) for s in np.ravel(shape)]
    if len(dims) == 1:
        dims.append(1)
    while len(dims) > 2 and dims[-1] == 1:
        dims.pop()
    return np.reshape(np.asarray(x), dims, order="F")


def vec(x, dtype=np.float64) -> np.ndarray:
    """Flatten a size/parameter argument (``N_u(:)'``) to a 1-D array."""
    return np.asarray(x, dtype=dtype).ravel(order="F")


def scalar(x):
    """Python scalar from a scalar-like argument (numbers, 0-d or 1-element arrays)."""
    return np.asarray(x).item()


def single(x) -> np.ndarray:
    """MATLAB ``single``: float32, or complex64 when complex."""
    x = np.asarray(x)
    return x.astype(np.complex64 if np.iscomplexobj(x) else np.float32, copy=False)


def double(x) -> np.ndarray:
    """MATLAB ``double``: float64, or complex128 when complex."""
    x = np.asarray(x)
    return x.astype(np.complex128 if np.iscomplexobj(x) else np.float64, copy=False)


def fix(x):
    """MATLAB ``fix`` (round toward zero)."""
    return np.trunc(x)


def mround(x):
    """MATLAB ``round`` (half away from zero), also used by integer casts."""
    x = np.asarray(x)
    return np.sign(x) * np.floor(np.abs(x) + 0.5)


def int32(x) -> np.ndarray:
    """MATLAB ``int32`` cast: round half away from zero, then saturate."""
    info = np.iinfo(np.int32)
    return np.clip(mround(x), info.min, info.max).astype(np.int32)


def mixed(op, a, b):
    """MATLAB arithmetic between single and double operands.

    MATLAB evaluates ``single op double`` in double precision and rounds the
    result to single (verified on R2024b), whereas NumPy casts the double
    operand to float32 first. ``mixed`` reproduces MATLAB.
    """
    single_out = is_single(a) or is_single(b)
    res = op(double(a), double(b))
    return single(res) if single_out else res


def squeeze(x) -> np.ndarray:
    """MATLAB ``squeeze``: drop singleton dims, keep at least 2 dims (n -> n x 1)."""
    x = np.asarray(x)
    if x.ndim <= 2:
        return x
    dims = [d for d in x.shape if d != 1]
    if not dims:
        dims = [1, 1]
    elif len(dims) == 1:
        dims = [dims[0], 1]
    return np.reshape(x, dims, order="F")


def disp(msg: str = " ") -> None:
    """MATLAB ``disp``: progress messages printed by the upstream functions."""
    print(msg)


def num2str_row(v) -> str:
    """Approximation of MATLAB ``num2str`` for a numeric row vector."""
    return "  ".join(f"{x:g}" for x in np.ravel(v))


def is_single(x) -> bool:
    return np.asarray(x).dtype in (np.float32, np.complex64)


def imsize_ints(res):
    """``(im, imDim, imSize)`` from ``bmImReshape`` with Python ints for indexing."""
    im, imDim, imSize = res[:3]
    return im, int(imDim), tuple(int(s) for s in np.ravel(imSize))
