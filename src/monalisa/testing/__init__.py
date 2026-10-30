"""Tools to validate the port against MATLAB golden recordings.

The MATLAB side (``tools/matlab_capture``) records inputs and outputs of
upstream function calls to ``fixtures/matlab/<scenario>/<func>/call_NNN.mat``.
This package loads these records, converts them to the Python conventions,
replays them against the ported functions and compares the results.
"""

from monalisa.testing.fixtures import Record, from_matlab, iter_records, load_record
from monalisa.testing.parity import Tolerance, compare, replay

__all__ = [
    "Record",
    "Tolerance",
    "compare",
    "from_matlab",
    "iter_records",
    "load_record",
    "replay",
]
