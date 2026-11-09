"""Centered FFT along the first axes, as MATLAB fftshift(fft(ifftshift(x, n), [], n), n) per axis."""

from monalisa._fft import fftshift, ifftshift


def centered_fft(x, n_axes, transform):
    """``fftshift(transform(ifftshift(x)))`` along axes ``0 .. n_axes-1``, one 1-D transform per axis.

    The shifts are permutations along their own axis and commute with the transforms along the
    other axes, so shifting all axes at once gives the same values as shifting around each 1-D
    transform (bit for bit), with two copies instead of two per axis.
    """
    axes = tuple(range(n_axes))
    x = ifftshift(x, axes)
    for n in axes:
        x = transform(x, axis=n, workers=-1, overwrite_x=True)
    return fftshift(x, axes)
