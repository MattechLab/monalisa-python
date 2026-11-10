"""Argument defaults shared by the functions (MATLAB ``varargin`` handling) and the clock.
"""

from monalisa.util._default_grid import default_grid
from monalisa.util._default_kernel import default_kernel
from monalisa.util._default_sparse_type import default_sparse_type
from monalisa.util._time_in_second import time_in_second
from monalisa.util._varargin import varargin

__all__ = [
    "default_grid",
    "default_kernel",
    "default_sparse_type",
    "time_in_second",
    "varargin",
]
