"""Port of src/gridding123/m/bmGridder_n2u_leight.m."""

import numpy as np

from monalisa._mat import double, msize, reshape, single, vec
from monalisa.arrayUtility.bmPointReshape import bmPointReshape
from monalisa.gridding123.mex._gridder_n2u_leight import (
    bmGridder_n2u_leight1_mex,
    bmGridder_n2u_leight2_mex,
    bmGridder_n2u_leight3_mex,
)
from monalisa.varargin.bmVarargin_kernelType_nWin_kernelParam import (
    bmVarargin_kernelType_nWin_kernelParam,
)


def _div_single(a, b):
    # MATLAB single/double: computed in double, rounded to single
    return (a.astype(np.float64) / b).astype(np.float32)


def bmGridder_n2u_leight(y, t, v, N_u, dK_u, kernelType=None, nWin=None, kernelParam=None):
    """Grid non-uniform data ``y`` ``[nCh, nPt]`` onto the uniform grid ``N_u``.

    Density-compensated (``v``) Gaussian gridding with per-cell
    normalization. Returns ``[nCh, N_u]`` complex single. Like the MEX
    implementation, the kernel is Gaussian with width ``kernelParam[0]``
    whatever ``kernelType`` is.
    """
    _, nWin, kernelParam = bmVarargin_kernelType_nWin_kernelParam(kernelType, nWin, kernelParam)
    t = single(bmPointReshape(t)).copy()
    y = single(bmPointReshape(y))
    v = single(bmPointReshape(v))
    nCh = msize(y, 1)
    imDim = msize(t, 1)
    N_u = double(vec(N_u))
    dK_u = double(vec(dK_u))
    nWin = vec(nWin)
    kernelParam = vec(kernelParam)

    shift = np.trunc(N_u[:imDim] / 2 + 1)
    for d in range(imDim):
        t[d, :] = _div_single(t[d, :], dK_u[d])
        v = _div_single(v, dK_u[d])
    t = (t.astype(np.float64) + shift[:, None]).astype(np.float32)

    temp_mask = np.zeros(t.shape[1], dtype=bool)
    for d in range(imDim):
        temp_mask |= (t[d, :] < 1) | (t[d, :] > N_u[d])
    keep = ~temp_mask
    t = np.ascontiguousarray(t[:, keep])
    y = y[:, keep]
    v = np.ascontiguousarray(v[0, keep])

    yRe = np.ascontiguousarray(y.real, dtype=np.float32)
    yIm = np.ascontiguousarray(y.imag, dtype=np.float32) if np.iscomplexobj(y) else np.zeros_like(yRe)
    N = [int(n) for n in N_u[:imDim]]
    nW = int(nWin[0])
    kp1 = np.float32(kernelParam[0])
    if imDim == 1:
        bRe, bIm = bmGridder_n2u_leight1_mex(yRe, yIm, t[0], v, N[0], nW, kp1)
    elif imDim == 2:
        bRe, bIm = bmGridder_n2u_leight2_mex(yRe, yIm, t[0], t[1], v, N[0], N[1], nW, kp1)
    elif imDim == 3:
        bRe, bIm = bmGridder_n2u_leight3_mex(yRe, yIm, t[0], t[1], t[2], v, N[0], N[1], N[2], nW, kp1)
    else:
        raise ValueError("bmGridder_n2u_leight: imDim must be 1, 2 or 3")

    data_u = (bRe + 1j * bIm).astype(np.complex64)
    return reshape(data_u, [nCh, *N])
