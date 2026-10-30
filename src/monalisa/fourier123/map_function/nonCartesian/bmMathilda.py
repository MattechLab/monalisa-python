"""Port of src/fourier123/map_function/nonCartesian/bmMathilda.m."""

import numpy as np

from monalisa._mat import disp, double, int32, isempty, msize, num2str_row, reshape, single, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmPointReshape import bmPointReshape
from monalisa.coilSense.map.bmCoilSense_pinv import bmCoilSense_pinv
from monalisa.fourier1.bmIDF1 import bmIDF1
from monalisa.fourier2.bmIDF2 import bmIDF2
from monalisa.fourier3.bmIDF3 import bmIDF3
from monalisa.fourier123.prep_function.bmK import bmK
from monalisa.gridding123.m.bmGridder_n2u_leight import bmGridder_n2u_leight
from monalisa.image123.bmImCrope import bmImCrope
from monalisa.varargin.bmVarargin_kernelType_nWin_kernelParam import (
    bmVarargin_kernelType_nWin_kernelParam,
)
from monalisa.varargin.bmVarargin_N_u_dK_u import bmVarargin_N_u_dK_u


def bmMathilda(y, t, v, C=None, N_u=None, n_u=None, dK_u=None, kernelType=None, nWin=None,
               kernelParam=None, fft_lib_flag=None, leight_flag=None):
    """Gridded reconstruction of non-Cartesian data.

    Density-compensated gridding of ``y`` (trajectory ``t``, volume elements
    ``v``) on the grid ``N_u`` with step ``dK_u``, centered inverse FFT,
    deapodization, cropping to ``n_u`` and, when coil sensitivities ``C``
    are given, coil combination. Without ``C`` one image per channel is
    returned (block format ``[n_u, nCh]``). Output is complex single.
    """
    kernelType, nWin, kernelParam = bmVarargin_kernelType_nWin_kernelParam(kernelType, nWin, kernelParam)
    N_u, dK_u = bmVarargin_N_u_dK_u(t, N_u, dK_u)
    if isempty(n_u):
        n_u = N_u
    if isempty(fft_lib_flag):
        fft_lib_flag = "MATLAB"
    if isempty(leight_flag):
        leight_flag = True
    if fft_lib_flag != "MATLAB":
        raise NotImplementedError("bmMathilda: only fft_lib_flag='MATLAB' is available in Python")
    if np.sum(np.mod(vec(N_u), 2)) > 0:
        raise ValueError("N_u must have all components even for the Fourier transform. ")

    y = np.asarray(y)
    if msize(y, 1) >= msize(y, 2):
        y = y.T
    t = double(bmPointReshape(t))
    y = single(bmPointReshape(y))
    v = double(bmPointReshape(v))
    C = None if isempty(C) else single(C)

    N_u = double(int32(vec(N_u)))
    n_u = double(int32(vec(n_u)))
    dK_u = double(single(vec(dK_u)))
    N_u_single = single(N_u)
    dK_u_single = single(dK_u)
    nWin = double(vec(nWin))
    kernelParam = double(vec(kernelParam))
    imDim = msize(t, 1)
    nCh = msize(y, 1)

    disp(" ")
    disp("This is Mathilda...  ")
    disp(f"Matrix size  {num2str_row(N_u_single)} . ")
    disp(f"FoV          {num2str_row(1.0 / dK_u_single)} . ")
    disp(" ")

    if not leight_flag:
        raise NotImplementedError("bmMathilda: the deprecated bmGridder_n2u path is not ported yet")
    x = bmGridder_n2u_leight(y, t, v, N_u, dK_u, kernelType, nWin, kernelParam)

    x = reshape(x, [nCh, np.prod(N_u)])
    x = x.T
    x = bmBlockReshape(x, N_u)
    idf = {1: bmIDF1, 2: bmIDF2, 3: bmIDF3}[imDim]
    x = idf(x, N_u, dK_u)

    K = single(bmK(N_u_single, dK_u_single, nCh, kernelType, nWin, kernelParam))
    K = bmBlockReshape(K, N_u)
    x = x * K

    if not np.array_equal(N_u, n_u):
        x = bmImCrope(x, N_u, n_u)
    if C is not None:
        C = bmBlockReshape(C, n_u)
        x = bmCoilSense_pinv(C, x, n_u)
    return x
