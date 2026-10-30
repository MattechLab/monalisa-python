"""Port of src/fourierN/bmIDF.m."""

import numpy as np
import scipy.fft

from monalisa._mat import fix, isempty, mixed, msize, ndims


def bmIDF(f, k, nZero=None, nDim=None, gridType=None, nargout=1):
    """Inverse discrete Fourier transform of ``f`` along dimension ``nDim`` (1-based)
    sampled on the frequency grid ``k`` (or with step ``k`` when scalar).

    Returns ``iFf`` or ``(iFf, x, outGridType)``. Grid types follow upstream:
    0 odd centered, 1/2 even shifted right/left, 3 even symmetric, 4 general.
    """
    f = np.asarray(f)
    if isempty(nDim):
        nDim = 1
        while msize(f, nDim) == 1 and nDim < ndims(f):
            nDim += 1
    nDim = int(nDim)
    k = np.asarray(k, dtype=np.float64)
    if k.size == 1:
        dK = float(k.ravel()[0])
        N = msize(f, nDim)
        M = fix(N / 2)
        k = np.arange(-M, N - M) * dK
    else:
        k = k.ravel(order="F")
    nZero = 0 if isempty(nZero) else nZero
    nZero = int(2 * fix(nZero / 2))
    if isempty(gridType):
        gridType = 0 if abs(np.mean(k)) < abs(k[1] - k[0]) / 4 else 2
    N = k.size
    dK = k[1] - k[0]
    G = k[-1] - k[0] + dK
    dX = 1 / G
    m = np.mean(k)
    err = (
        dK <= 0
        or (N % 2 and gridType not in (0, 4))
        or (N % 2 and abs(m) > dK / 4 and gridType != 4)
        or (N % 2 and abs(m) < dK / 4 and gridType not in (0, 4))
        or (N % 2 == 0 and gridType not in (1, 2, 3, 4))
        or (N % 2 == 0 and abs(m) > dK / 4 and gridType not in (1, 2, 4))
        or (N % 2 == 0 and abs(m) < dK / 4 and gridType not in (3, 4))
        or (N % 2 == 0 and m > dK / 4 and gridType not in (1, 4))
        or (N % 2 == 0 and m < -dK / 4 and gridType not in (2, 4))
        or (abs(m) > dK * 3 / 4 and gridType != 4)
        or k.size != msize(f, nDim)
    )
    if err:
        raise ValueError("The grid is not consitent with other inputs")

    ax = nDim - 1
    while f.ndim <= ax:
        f = f[..., None]
    if nZero > 0:
        N = k.size + nZero
        k = np.arange(N) * dK + k[0] - dK * nZero / 2
        G = k[-1] - k[0] + dK
        dX = 1 / G
        zshape = list(f.shape)
        zshape[ax] = nZero // 2
        z = np.zeros(zshape, dtype=f.dtype)
        f = np.concatenate([z, f, z], axis=ax)

    def cifft(a):
        a = scipy.fft.ifft(scipy.fft.ifftshift(a, axes=ax), axis=ax, workers=-1)
        return scipy.fft.fftshift(a, axes=ax)

    M = int(fix(N / 2))
    shape_ph = [1] * f.ndim
    shape_ph[ax] = N
    if gridType in (0, 2):
        iFf = mixed(np.multiply, cifft(f), N * dK)
        x = np.arange(-M, N - M) * dX
        outGridType = 0 if N % 2 else 2
    elif gridType == 1:
        iFf = mixed(np.multiply, cifft(np.roll(f, 1, axis=ax)), N * dK)
        iFf = np.roll(iFf, -1, axis=ax)
        x = np.arange(-(M - 1), M + 1) * dX
        outGridType = 1
    elif gridType == 3:
        iFf = mixed(np.multiply, cifft(f), N * dK)
        myPhase = np.reshape(np.arange(-M, N - M) / N, shape_ph)
        iFf = np.exp(1j * np.pi * myPhase) * iFf
        x = np.arange(-M, N - M) * dX
        outGridType = 2
    elif gridType == 4:
        iFf = mixed(np.multiply, scipy.fft.fftshift(scipy.fft.ifft(f, axis=ax, workers=-1), axes=ax), N * dK)
        myPhase = np.reshape(np.arange(-M, N - M).astype(np.float64), shape_ph)
        iFf = np.exp(1j * 2 * np.pi * k[0] * dX * myPhase) * iFf
        x = np.arange(-M, N - M) * dX
        outGridType = 0 if N % 2 else 2
    else:
        raise ValueError("The grid is not consitent with other inputs")
    if nargout <= 1:
        return iFf
    return (iFf, x[None, :], float(outGridType))[:nargout]
