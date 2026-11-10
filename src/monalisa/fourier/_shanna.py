"""Port of src/fourier123/map_function/nonCartesian/bmShanna.m."""

from monalisa.fourier._shanna_matlab import shanna_matlab


def shanna(x, G, KFC, n_u, fft_lib_sFlag):
    """Forward non-Cartesian Fourier model; only the ``'MATLAB'`` FFT backend exists in Python."""
    if fft_lib_sFlag != "MATLAB":
        raise NotImplementedError(f"shanna: fft_lib_sFlag {fft_lib_sFlag!r} is not available in Python")
    return shanna_matlab(x, G, KFC, n_u)
