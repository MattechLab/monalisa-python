"""Port of src/fourier123/map_function/nonCartesian/bmShanna.m."""

from monalisa.fourier123.map_function.nonCartesian.bmShanna_MATLAB import bmShanna_MATLAB


def bmShanna(x, G, KFC, n_u, fft_lib_sFlag):
    """Forward non-Cartesian Fourier model; only the ``'MATLAB'`` FFT backend exists in Python."""
    if fft_lib_sFlag != "MATLAB":
        raise NotImplementedError(f"bmShanna: fft_lib_sFlag {fft_lib_sFlag!r} is not available in Python")
    return bmShanna_MATLAB(x, G, KFC, n_u)
