"""Port of src/coilSense/nonCart/bmCoilSense_nonCart_secondary.m."""

import numpy as np

from monalisa._mat import disp, mixed, msize, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmCol import bmCol
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.fourier123.map_function.nonCartesian.bmNakatsha import bmNakatsha
from monalisa.fourier123.map_function.nonCartesian.bmNasha import bmNasha
from monalisa.fourier123.map_function.nonCartesian.bmShanna import bmShanna
from monalisa.fourier123.prep_function.bmKF import bmKF
from monalisa.fourier123.prep_function.bmKF_conj import bmKF_conj
from monalisa.image123.bmImPseudoDiffusion import bmImPseudoDiffusion
from monalisa.linSpace.bmY_norm import bmY_norm
from monalisa.linSpace.bmY_ve_reshape import bmY_ve_reshape


def _dot(a, b):
    """MATLAB ``a(:)' * b(:)``."""
    return np.vdot(np.ravel(a, order="F"), np.ravel(b, order="F"))


def bmCoilSense_nonCart_secondary(y, C, y_ref, C_ref, Gn, Gu, Gut, ve, nIter, display_flag=False, nargout=1):
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
    norm_ref = bmY_norm(y_ref, ve)
    mean_norm = np.mean(bmCol(bmY_norm(y, ve, False)))
    y_ref = mixed(np.multiply, y_ref, nCh_array) / norm_ref * mean_norm
    y = np.concatenate([np.reshape(y_ref, (-1, 1), order="F"), y], axis=1)
    C = np.concatenate([np.reshape(C_ref, (-1, 1), order="F"), bmColReshape(C, N_u)], axis=1)
    x = bmColReshape(bmNasha(y, Gn, N_u, C), N_u)

    nCh = msize(y, 2)
    ve = bmY_ve_reshape(ve, msize(y))
    KF = bmKF(None, N_u, N_u, dK_u, nCh, Gu.kernel_type, Gu.nWin, Gu.kernelParam)
    KF_conj = bmKF_conj(None, N_u, N_u, dK_u, nCh, Gu.kernel_type, Gu.nWin, Gu.kernelParam)
    myZero = np.zeros(int(np.prod(N_u)))
    for i in range(int(nIter)):
        v = bmShanna(x, Gu, KF * C, N_u, "MATLAB") - y
        w = bmNakatsha(mixed(np.multiply, ve, v), Gut, KF_conj, False, N_u, "MATLAB")
        d = 2 * np.sum(np.conj(C) * w, axis=1, keepdims=True)
        Ad = bmShanna(d, Gu, KF * C, N_u, "MATLAB")
        lam = np.real(_dot(Ad, mixed(np.multiply, ve, v))) / np.real(_dot(Ad, mixed(np.multiply, ve, Ad)))
        x = x - lam * d
        d_C = 2 * np.tile(np.conj(x), (1, nCh)) * w
        d_C[:, 0] = myZero
        Ad_C = bmShanna(x, Gu, KF * d_C, N_u, "MATLAB")
        num = np.real(_dot(Ad_C, mixed(np.multiply, ve, v)))
        lam_C = num / np.real(_dot(Ad_C, mixed(np.multiply, ve, Ad_C)))
        C = C - lam_C * d_C
        disp(f"Iteration {i + 1} of gradient descent done.")

    C = C[:, 1:]
    nCh = msize(C, 2)
    shape = [int(n) for n in N_u]
    C = np.array(np.reshape(C, [*shape, nCh], order="F"))
    x = bmBlockReshape(x, N_u)
    for i in range(nCh):
        C[..., i] = bmImPseudoDiffusion(C[..., i], nIterSmooth)
    C = bmBlockReshape(mixed(np.multiply, C, nCh_array), N_u)
    if nargout > 1:
        return C, x
    return C
