"""Port of src/coilSense/nonCart/bmCoilSense_nonCart_primary.m."""

import numpy as np

from monalisa._mat import mixed, msize, numel, vec
from monalisa.array._block_reshape import block_reshape
from monalisa.array._col import col
from monalisa.image._im_laplace_equation_solver import im_laplace_equation_solver
from monalisa.image._im_pseudo_diffusion_in_mask import im_pseudo_diffusion_in_mask
from monalisa.optim._y_norm import y_norm
from monalisa.recon._nasha import nasha


def coil_sense_non_cart_primary(y, y_ref, C_ref, Gn, ve, m):
    """First estimate of the coil sensitivities of the array ``y`` relative to
    the reference coil (``y_ref``, ``C_ref``), smoothed in the mask ``m`` and
    harmonically extended outside."""
    nIter_smooth = 2
    L_nIter = 1000
    L_th = 1e-4
    N_u = vec(Gn.N_u)
    shape = [int(n) for n in N_u]
    nPt = int(Gn.r_size)
    nCh = int(numel(y) / nPt)
    nCh_array = msize(y, 2)
    y = np.asarray(y)
    norm_ref = y_norm(y_ref, ve)
    mean_norm = np.mean(col(y_norm(y, ve, False)))
    y_ref = mixed(np.multiply, np.asarray(y_ref), nCh_array) / norm_ref * mean_norm
    x_ref = block_reshape(nasha(y_ref, Gn, N_u), N_u)
    x = np.reshape(nasha(y, Gn, N_u), [*shape, nCh], order="F")
    m = np.reshape(np.asarray(m, dtype=bool), shape, order="F")
    m_neg = ~m
    with np.errstate(divide="ignore", invalid="ignore"):
        anat_ref = x_ref / C_ref
    anat_ref[m_neg] = 1
    C = np.zeros([*shape, nCh], dtype=np.complex64, order="F")
    for i in range(nCh):
        with np.errstate(divide="ignore", invalid="ignore"):
            temp_im = im_pseudo_diffusion_in_mask(x[..., i] / anat_ref, m, nIter_smooth)
        temp_im[m_neg] = 0
        C[..., i] = im_laplace_equation_solver(temp_im, m, L_nIter, L_th, "omp")
    C = mixed(np.multiply, C, nCh_array)
    return block_reshape(C, N_u)
