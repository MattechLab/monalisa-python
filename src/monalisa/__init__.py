"""Monalisa: Python port of the MattechLab MRI reconstruction toolbox.

Every MATLAB function ``bmFoo`` of the upstream ``src/`` tree is ported to a
module ``monalisa/<folder>/bmFoo.py`` defining a function of the same name.
All ported functions are also reachable from the top-level package::

    import monalisa as ml
    x = ml.bmMathilda(y, t, ve, C, N_u, n_u, dK_u)
"""

from __future__ import annotations

import importlib
from functools import lru_cache
from pathlib import Path

__version__ = "0.1.0.dev0"

UPSTREAM_COMMIT = "0cb5cf93c699870bcd93a00b2e2cd787bef73fcc"


@lru_cache(maxsize=1)
def _function_index() -> dict[str, str]:
    """Map ported function names to their module paths, without importing them."""
    root = Path(__file__).parent
    index = {}
    for path in root.rglob("bm*.py"):
        rel = path.relative_to(root).with_suffix("")
        index[path.stem] = "monalisa." + ".".join(rel.parts)
    return index


def find_function(name: str):
    """Return the ported function ``name``, or ``None`` if it is not ported yet."""
    module = _function_index().get(name)
    if module is None:
        return None
    return getattr(importlib.import_module(module), name)


def __getattr__(name: str):
    func = find_function(name)
    if func is None:
        raise AttributeError(f"module 'monalisa' has no attribute {name!r}")
    return func


def __dir__():
    return sorted(set(globals()) | set(_function_index()))
