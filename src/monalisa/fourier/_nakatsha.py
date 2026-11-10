"""Port of src/fourier123/map_function/nonCartesian/bmNakatsha.m."""

from monalisa._mat import isempty
from monalisa.fourier._nakatsha_matlab import nakatsha_matlab


def nakatsha(y, G, KFC_conj, C_flag, n_u, fft_lib_sFlag):
    """Adjoint non-Cartesian Fourier model; only the ``'MATLAB'`` FFT backend exists in Python."""
    if isempty(n_u):
        n_u = G.N_u
    if fft_lib_sFlag != "MATLAB":
        raise NotImplementedError(f"nakatsha: fft_lib_sFlag {fft_lib_sFlag!r} is not available in Python")
    return nakatsha_matlab(y, G, KFC_conj, C_flag, n_u)
