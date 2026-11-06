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
    # single-precision inner products of ~1e5 terms: BLAS summation order differs
    # (MATLAB uses MKL, NumPy OpenBLAS), relative differences ~1e-5 on the scalar
    "bmEuclideProd": Tolerance(rel_l2=1e-4, rtol=1e-4),
    "bmSquaredNorm": Tolerance(rel_l2=1e-4, rtol=1e-4),
}

# Record ids ("scenario/func/call_NNN") or function names that are expected
# to differ from MATLAB, with the reason. Keep this list short and justified.
KNOWN_DIVERGENCES: dict[str, str] = {
    "bmTimeInSecond": "wall-clock time, not reproducible",
    "bmCheckDir": "depends on the file system state at recording time",
    "bmCreateDir": "depends on the file system state (and would create the recorded directories)",
    # MATLAB's imregdemons (Image Processing Toolbox) is replaced by SimpleITK's demons:
    # same algorithm, fields equal in quality but not to rounding. Validated on registration
    # quality and on the motion-compensated reconstructions: tests/validation/test_registration_vs_matlab.py,
    # docs/validation_registration.md.
    "bmImDeformFieldChain_imRegDemons23": "open-source demons (SimpleITK) instead of imregdemons",
    "bmImDeformFieldSheet_imRegDemons23": "open-source demons (SimpleITK) instead of imregdemons",
}


def tolerance_for(func: str) -> Tolerance:
    return TOLERANCES.get(func, Tolerance())
