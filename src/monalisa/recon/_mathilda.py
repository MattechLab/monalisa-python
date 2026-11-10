"""Port of src/fourier123/map_function/nonCartesian/bmMathilda.m."""

import numpy as np

from monalisa._mat import disp, double, int32, isempty, msize, num2str_row, reshape, single, vec
from monalisa.array._block_reshape import block_reshape
from monalisa.array._point_reshape import point_reshape
from monalisa.coil._coil_sense_pinv import coil_sense_pinv
from monalisa.fourier._deapodization import deapodization
from monalisa.fourier._idf1 import idf1
from monalisa.fourier._idf2 import idf2
from monalisa.fourier._idf3 import idf3
from monalisa.gridding._gridder_n2u_leight import gridder_n2u_leight
from monalisa.image._im_crop import im_crop
from monalisa.util._default_grid import default_grid
from monalisa.util._default_kernel import default_kernel


def mathilda(y, t, v, C=None, N_u=None, n_u=None, dK_u=None, kernelType=None, nWin=None,
             kernelParam=None, fft_lib_flag=None, leight_flag=None):
    """Gridded reconstruction of non-Cartesian data.

    Density-compensated gridding of ``y`` (trajectory ``t``, volume elements
    ``v``) on the grid ``N_u`` with step ``dK_u``, centered inverse FFT,
    deapodization, cropping to ``n_u`` and, when coil sensitivities ``C``
    are given, coil combination. Without ``C`` one image per channel is
    returned (block format ``[n_u, nCh]``). Output is complex single.
    """
    kernelType, nWin, kernelParam = default_kernel(kernelType, nWin, kernelParam)
    N_u, dK_u = default_grid(t, N_u, dK_u)
    if isempty(n_u):
        n_u = N_u
    if isempty(fft_lib_flag):
        fft_lib_flag = "MATLAB"
    if isempty(leight_flag):
        leight_flag = True
    if fft_lib_flag != "MATLAB":
        raise NotImplementedError("mathilda: only fft_lib_flag='MATLAB' is available in Python")
    if np.sum(np.mod(vec(N_u), 2)) > 0:
        raise ValueError("N_u must have all components even for the Fourier transform. ")

    y = np.asarray(y)
    if msize(y, 1) >= msize(y, 2):
        y = y.T
    t = double(point_reshape(t))
    y = single(point_reshape(y))
    v = double(point_reshape(v))
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
        raise NotImplementedError("mathilda: the deprecated bmGridder_n2u path is not ported yet")
    x = gridder_n2u_leight(y, t, v, N_u, dK_u, kernelType, nWin, kernelParam)

    x = reshape(x, [nCh, np.prod(N_u)])
    x = np.asfortranarray(x.T)  # MATLAB x.' copies: [prod(N_u), nCh] in column order
    x = block_reshape(x, N_u)
    idf = {1: idf1, 2: idf2, 3: idf3}[imDim]
    x = idf(x, N_u, dK_u)

    K = single(deapodization(N_u_single, dK_u_single, nCh, kernelType, nWin, kernelParam))
    K = block_reshape(K, N_u)
    x = x * K

    if not np.array_equal(N_u, n_u):
        x = im_crop(x, N_u, n_u)
    if C is not None:
        C = block_reshape(C, n_u)
        x = coil_sense_pinv(C, x, n_u)
    return x
