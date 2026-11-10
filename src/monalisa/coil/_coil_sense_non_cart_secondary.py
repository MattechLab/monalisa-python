"""Port of src/coilSense/nonCart/bmCoilSense_nonCart_secondary.m."""

import numpy as np

from monalisa._mat import disp, mixed, msize, vec
from monalisa.array._block_reshape import block_reshape
from monalisa.array._col import col
from monalisa.array._col_reshape import col_reshape
from monalisa.fourier._kf import kf
from monalisa.fourier._kf_conj import kf_conj
from monalisa.fourier._nakatsha import nakatsha
from monalisa.fourier._shanna import shanna
from monalisa.image._im_pseudo_diffusion import im_pseudo_diffusion
from monalisa.optim._y_norm import y_norm
from monalisa.optim._y_ve_reshape import y_ve_reshape
from monalisa.recon._nasha import nasha


def _dot(a, b):
    """MATLAB ``a(:)' * b(:)``."""
    return np.vdot(np.ravel(a, order="F"), np.ravel(b, order="F"))


def coil_sense_non_cart_secondary(y, C, y_ref, C_ref, Gn, Gu, Gut, ve, nIter, display_flag=False, nargout=1):
    """Refine the coil sensitivities ``C`` jointly with the image by
    ``nIter`` alternating gradient steps on the data consistency of all coils
    (reference coil included and kept fixed). Returns ``C`` or ``(C, x)``."""
    nIterSmooth = 2
    y = np.asarray(y)
    y_ref = np.asarray(y_ref)
    if y.dtype not in (np.float32, np.complex64):
        raise TypeError("y must be of class 'single' .")
    if y_ref.dtype not in (np.float32, np.complex64):
        raise TypeError("y_ref must be of class 'single' .")
    N_u = vec(Gn.N_u)
    dK_u = vec(Gn.d_u)
    nCh_array = msize(y, 2)
    C = mixed(np.divide, np.asarray(C), nCh_array)
    norm_ref = y_norm(y_ref, ve)
    mean_norm = np.mean(col(y_norm(y, ve, False)))
    y_ref = mixed(np.multiply, y_ref, nCh_array) / norm_ref * mean_norm
    y = np.concatenate([np.reshape(y_ref, (-1, 1), order="F"), y], axis=1)
    C = np.concatenate([np.reshape(C_ref, (-1, 1), order="F"), col_reshape(C, N_u)], axis=1)
    x = col_reshape(nasha(y, Gn, N_u, C), N_u)

    nCh = msize(y, 2)
    ve = y_ve_reshape(ve, msize(y))
    KF = kf(None, N_u, N_u, dK_u, nCh, Gu.kernel_type, Gu.nWin, Gu.kernelParam)
    KF_conj = kf_conj(None, N_u, N_u, dK_u, nCh, Gu.kernel_type, Gu.nWin, Gu.kernelParam)
    myZero = np.zeros(int(np.prod(N_u)))
    for i in range(int(nIter)):
        v = shanna(x, Gu, KF * C, N_u, "MATLAB") - y
        w = nakatsha(mixed(np.multiply, ve, v), Gut, KF_conj, False, N_u, "MATLAB")
        d = 2 * np.sum(np.conj(C) * w, axis=1, keepdims=True)
        Ad = shanna(d, Gu, KF * C, N_u, "MATLAB")
        lam = np.real(_dot(Ad, mixed(np.multiply, ve, v))) / np.real(_dot(Ad, mixed(np.multiply, ve, Ad)))
        x = x - lam * d
        d_C = 2 * np.conj(x) * w  # MATLAB 2 * repmat(conj(x), [1, nCh]) .* w: same products
        d_C[:, 0] = myZero
        Ad_C = shanna(x, Gu, KF * d_C, N_u, "MATLAB")
        num = np.real(_dot(Ad_C, mixed(np.multiply, ve, v)))
        lam_C = num / np.real(_dot(Ad_C, mixed(np.multiply, ve, Ad_C)))
        C = C - lam_C * d_C
        disp(f"Iteration {i + 1} of gradient descent done.")

    C = C[:, 1:]
    nCh = msize(C, 2)
    shape = [int(n) for n in N_u]
    C = np.array(np.reshape(C, [*shape, nCh], order="F"))
    x = block_reshape(x, N_u)
    for i in range(nCh):
        C[..., i] = im_pseudo_diffusion(C[..., i], nIterSmooth)
    C = block_reshape(mixed(np.multiply, C, nCh_array), N_u)
    if nargout > 1:
        return C, x
    return C
