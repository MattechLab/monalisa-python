"""Port of src/fourier123/prep_function/bmK.m."""

import numpy as np
import scipy.special

from monalisa._mat import double, int32, single, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.fourier1.bmDFT1 import bmDFT1
from monalisa.fourier2.bmDFT2 import bmDFT2
from monalisa.fourier3.bmDFT3 import bmDFT3
from monalisa.varargin.bmVarargin_kernelType_nWin_kernelParam import (
    bmVarargin_kernelType_nWin_kernelParam,
)


def _normpdf(d, sigma):
    return np.exp(-0.5 * (d / sigma) ** 2) / (np.sqrt(2 * np.pi) * sigma)


def bmK(N_u, dK_u, nCh, kernelType=None, nWin=None, kernelParam=None):
    """Deapodization kernel of the gridding kernel, in column format
    ``[prod(N_u), nCh]`` (single), clipped at ``K_max``."""
    arg_osf = 2
    kernelType, nWin, kernelParam = bmVarargin_kernelType_nWin_kernelParam(kernelType, nWin, kernelParam)
    N_u = double(int32(vec(N_u)))
    N_u_os = np.round(N_u * arg_osf)
    imDim = N_u.size
    dK_u = double(single(vec(dK_u)))  # noqa: F841 (kept for parity with MATLAB)
    nWin = double(single(vec(nWin)))
    kernelParam = double(single(vec(kernelParam)))
    nCh = int(double(single(nCh)))

    if np.sum(np.mod(N_u, 2)) > 0:
        raise ValueError("N_u must have all components even for the Fourier transform. ")

    axes = [np.arange(-N * arg_osf / 2, N * arg_osf / 2) / arg_osf for N in N_u]
    grids = np.meshgrid(*axes, indexing="ij")
    d = np.zeros(grids[0].shape)
    for g in grids:
        d = d + g**2
    d = np.sqrt(d)
    os_shape = [int(n) for n in N_u_os]

    if kernelType == "gauss":
        mySigma, K_max = kernelParam[0], kernelParam[1]
        myWeight = _normpdf(np.ravel(d, order="F"), mySigma)
    elif kernelType == "kaiser":
        myTau, myAlpha, K_max = kernelParam[0], kernelParam[1], kernelParam[2]
        I0myAlpha = scipy.special.i0(myAlpha)
        myWeight = np.maximum(1 - (np.ravel(d, order="F") / myTau) ** 2, 0)
        myWeight = myAlpha * np.sqrt(myWeight)
        myWeight = scipy.special.i0(myWeight) / I0myAlpha
    else:
        raise ValueError(f"Unknown kernelType {kernelType!r}")
    myWeight = np.array(bmBlockReshape(myWeight, N_u_os), dtype=np.float64)
    if imDim == 1:
        myWeight = myWeight.reshape(os_shape[0], order="F")

    nWin_half = np.trunc(nWin[0] / 2)
    if imDim == 1:
        # upstream bug kept for parity: the lower bound lacks its minus sign
        x = grids[0]
        myWeight[(x < nWin_half) | (x > nWin_half)] = 0
    else:
        for g in grids:
            myWeight[(g < -nWin_half) | (g > nWin_half)] = 0

    if imDim == 1:
        K = bmDFT1(myWeight[:, None], N_u_os, 1.0 / N_u)
    elif imDim == 2:
        K = bmDFT2(myWeight, N_u_os, 1.0 / N_u)
    else:
        K = bmDFT3(myWeight, N_u_os, 1.0 / N_u)

    sl = tuple(
        slice(int(Nos // 2 - N // 2), int(Nos // 2 + N // 2)) for Nos, N in zip(N_u_os, N_u, strict=True)
    )
    K = np.reshape(K, os_shape, order="F")[sl]

    K = np.abs(np.real(K))
    K = K / np.max(np.abs(K))
    K = 1.0 / K
    K = np.minimum(K, K_max)
    K = np.tile(np.reshape(K, (-1, 1), order="F"), (1, nCh))
    return single(K)
