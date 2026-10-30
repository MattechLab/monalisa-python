"""Per-function parity tolerances and documented divergences.

Defaults (monalisa.testing.parity.DEFAULT_TOL): single precision
rel_l2 <= 1e-5 and max_abs <= 1e-4 * max|ref|; double precision 1e-10 / 1e-8.
Every override must state why.
"""

from monalisa.testing import Tolerance

TOLERANCES: dict[str, Tolerance] = {
    # MATLAB interpolates single images in single precision and returns double;
    # the summation order of the separable cubic convolution differs.
    "bmImResize": Tolerance(rel_l2=1e-6, rtol=1e-5),
}

# Record ids ("scenario/func/call_NNN") or function names that are expected
# to differ from MATLAB, with the reason. Keep this list short and justified.
KNOWN_DIVERGENCES: dict[str, str] = {}


def tolerance_for(func: str) -> Tolerance:
    return TOLERANCES.get(func, Tolerance())
