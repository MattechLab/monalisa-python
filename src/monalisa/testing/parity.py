"""Comparison of Python results with MATLAB golden outputs."""

from __future__ import annotations

import copy
import inspect
from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg  # noqa: F401  (sp.linalg.norm)

from monalisa._mat import Struct, cell_items, cell_shape, iscell, msize
from monalisa.testing.fixtures import Record, from_matlab

# Default tolerances per MATLAB precision class: (relative L2, max abs error / max|ref|)
DEFAULT_TOL = {"single": (1e-5, 1e-4), "double": (1e-10, 1e-8)}


@dataclass(frozen=True)
class Tolerance:
    rel_l2: float | None = None
    rtol: float | None = None
    check_dtype: bool = True
    check_shape: bool = True

    def limits(self, precision: str) -> tuple[float, float]:
        rel_l2, rtol = DEFAULT_TOL.get(precision, DEFAULT_TOL["double"])
        return (
            self.rel_l2 if self.rel_l2 is not None else rel_l2,
            self.rtol if self.rtol is not None else rtol,
        )


def _precision(dtype) -> str:
    dtype = np.dtype(dtype)
    if dtype in (np.float32, np.complex64):
        return "single"
    if dtype in (np.float64, np.complex128):
        return "double"
    if dtype == np.bool_:
        return "logical"
    return dtype.name


def _describe(x) -> str:
    if x is None:
        return "None"
    if isinstance(x, np.ndarray):
        return f"ndarray{x.shape}{x.dtype}"
    return type(x).__name__


def _is_empty_ref(ml) -> bool:
    return ml is None or (isinstance(ml, np.ndarray) and ml.dtype != object and ml.size == 0)


_DEFAULT = Tolerance()


def compare(py, ml, tol: Tolerance = _DEFAULT, path: str = "out") -> list[str]:
    """Return a list of mismatch descriptions (empty when ``py`` matches ``ml``)."""
    if _is_empty_ref(ml):
        if py is None or (not isinstance(py, (str, Struct)) and np.size(py) == 0):
            return []
        return [f"{path}: expected empty, got {_describe(py)}"]

    if isinstance(ml, str):
        return [] if py == ml else [f"{path}: expected {ml!r}, got {py!r}"]

    if sp.issparse(ml):
        if not sp.issparse(py):
            return [f"{path}: expected sparse{ml.shape}, got {_describe(py)}"]
        if py.shape != ml.shape:
            return [f"{path}: sparse size {py.shape} != MATLAB {ml.shape}"]
        a, b = sp.csr_matrix(py, dtype=np.complex128), sp.csr_matrix(ml, dtype=np.complex128)
        rel_l2_max, _ = tol.limits(_precision(ml.dtype))
        nb = sp.linalg.norm(b)
        d = sp.linalg.norm(a - b)
        rel = d / nb if nb > 0 else d
        return [] if rel <= rel_l2_max else [f"{path}: sparse rel_l2={rel:.3e} (max {rel_l2_max:.0e})"]

    if hasattr(ml, "parity_fields"):
        if not hasattr(py, "parity_fields"):
            return [f"{path}: expected {type(ml).__name__}, got {_describe(py)}"]
        return compare(Struct(py.parity_fields()), Struct(ml.parity_fields()), tol, path)

    plain = (dict, np.ndarray, np.generic, bool, int, float, complex)
    if not isinstance(ml, plain) and hasattr(ml, "__dict__"):
        fields = {k: v for k, v in vars(ml).items() if not k.startswith("_")}
        return compare(py, Struct(fields), tol, path)

    if isinstance(ml, Struct):
        issues = []
        for key, val in ml.items():
            if key == "_class":
                continue
            if isinstance(py, dict):
                if key not in py:
                    issues.append(f"{path}.{key}: missing")
                    continue
                pv = py[key]
            elif hasattr(py, key):
                pv = getattr(py, key)
            else:
                issues.append(f"{path}.{key}: missing")
                continue
            issues += compare(pv, val, tol, f"{path}.{key}")
        return issues

    if isinstance(ml, np.ndarray) and ml.dtype == object:
        if not iscell(py):
            return [f"{path}: expected cell{ml.shape}, got {_describe(py)}"]
        if tol.check_shape and cell_shape(py) != msize(ml):
            return [f"{path}: cell size {cell_shape(py)} != MATLAB {msize(ml)}"]
        issues = []
        for i, (p, m) in enumerate(zip(cell_items(py), cell_items(ml), strict=True)):
            issues += compare(p, m, tol, f"{path}{{{i + 1}}}")
        return issues

    return _compare_numeric(py, np.asarray(ml), tol, path)


def _compare_numeric(py, ml: np.ndarray, tol: Tolerance, path: str) -> list[str]:
    python_scalar = isinstance(py, (bool, int, float, complex))
    pa = np.asarray(py)
    if pa.dtype == object:
        return [f"{path}: expected numeric {ml.dtype}, got object array"]

    issues = []
    if tol.check_shape:
        if pa.ndim == 1 and 1 in msize(ml) and len(msize(ml)) == 2:
            if pa.size != ml.size:
                issues.append(f"{path}: vector length {pa.size} != MATLAB {msize(ml)}")
        elif msize(pa) != msize(ml):
            issues.append(f"{path}: size {msize(pa)} != MATLAB {msize(ml)}")
    if issues:
        return issues

    p_ml = _precision(ml.dtype)
    p_py = "double" if python_scalar and not isinstance(py, bool) else _precision(pa.dtype)
    if tol.check_dtype and p_py != p_ml:
        issues.append(f"{path}: class {p_py} ({pa.dtype}) != MATLAB {p_ml} ({ml.dtype})")

    pa = pa.reshape(ml.shape, order="F") if pa.size == ml.size else pa
    if ml.dtype == np.bool_ or ml.dtype.kind in "iu":
        if not np.array_equal(pa, ml):
            n_bad = int(np.sum(pa != ml))
            issues.append(f"{path}: {n_bad}/{ml.size} values differ (exact comparison)")
        return issues

    rel_l2_max, rtol = tol.limits(p_ml)
    a = pa.astype(np.complex128 if np.iscomplexobj(pa) else np.float64)
    b = ml.astype(np.complex128 if np.iscomplexobj(ml) else np.float64)
    nan_a, nan_b = np.isnan(a), np.isnan(b)
    if not np.array_equal(nan_a, nan_b):
        issues.append(f"{path}: NaN pattern differs ({int(nan_a.sum())} vs {int(nan_b.sum())})")
        return issues
    inf_a, inf_b = np.isinf(a), np.isinf(b)
    if not np.array_equal(inf_a, inf_b) or not np.array_equal(a[inf_a], b[inf_b]):
        issues.append(f"{path}: Inf pattern differs")
        return issues
    ok = ~(nan_b | inf_b)
    diff = np.abs(a[ok] - b[ok])
    scale = float(np.max(np.abs(b[ok]))) if diff.size else 0.0
    norm_b = float(np.linalg.norm(b[ok]))
    rel_l2 = float(np.linalg.norm(diff)) / norm_b if norm_b > 0 else float(np.linalg.norm(diff))
    max_abs = float(diff.max()) if diff.size else 0.0
    if rel_l2 > rel_l2_max or max_abs > rtol * scale + np.finfo(np.float64).tiny:
        issues.append(
            f"{path}: rel_l2={rel_l2:.3e} (max {rel_l2_max:.0e}), "
            f"max_abs={max_abs:.3e} (max {rtol * scale:.3e}, ref max {scale:.3e})"
        )
    return issues


def replay(rec: Record, func, check_mutation: bool = True) -> list:
    """Call ``func`` with the recorded inputs and return ``rec.nargout`` outputs."""
    args = [from_matlab(a, "input") for a in rec.inputs]
    kwargs = {}
    if "nargout" in inspect.signature(func).parameters:
        kwargs["nargout"] = rec.nargout
    saved = copy.deepcopy(args) if check_mutation else None
    res = func(*args, **kwargs)
    if check_mutation:
        for i, (a, s) in enumerate(zip(args, saved, strict=True)):
            if compare(a, s, Tolerance(rel_l2=0.0, rtol=0.0), f"input{i + 1}") and s is not None:
                raise AssertionError(f"{rec.func} modified its input argument {i + 1} in place")
    if rec.nargout == 0:
        return []
    outs = list(res) if isinstance(res, tuple) else [res]
    if len(outs) < rec.nargout:
        raise AssertionError(f"{rec.func} returned {len(outs)} outputs, MATLAB call had {rec.nargout}")
    return outs[: rec.nargout]
