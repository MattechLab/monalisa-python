"""Port of src/fourier123/map_function/nonCartesian/bmNakatsha.m."""

from monalisa._mat import isempty
from monalisa.fourier123.map_function.nonCartesian.bmNakatsha_MATLAB import bmNakatsha_MATLAB


def bmNakatsha(y, G, KFC_conj, C_flag, n_u, fft_lib_sFlag):
    """Adjoint non-Cartesian Fourier model; only the ``'MATLAB'`` FFT backend exists in Python."""
    if isempty(n_u):
        n_u = G.N_u
    if fft_lib_sFlag != "MATLAB":
        raise NotImplementedError(f"bmNakatsha: fft_lib_sFlag {fft_lib_sFlag!r} is not available in Python")
    return bmNakatsha_MATLAB(y, G, KFC_conj, C_flag, n_u)
