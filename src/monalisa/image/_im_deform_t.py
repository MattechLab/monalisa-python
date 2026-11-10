"""Port of src/image123/bmImDeformT.m."""

from monalisa._mat import isempty, vec
from monalisa.array._block_reshape import block_reshape
from monalisa.array._col_reshape import col_reshape
from monalisa.array._is_block_shape import is_block_shape
from monalisa.fourier._dft1_conj_trans import dft1_conj_trans
from monalisa.fourier._dft2_conj_trans import dft2_conj_trans
from monalisa.fourier._dft3_conj_trans import dft3_conj_trans
from monalisa.fourier._idf1_conj_trans import idf1_conj_trans
from monalisa.fourier._idf2_conj_trans import idf2_conj_trans
from monalisa.fourier._idf3_conj_trans import idf3_conj_trans
from monalisa.sparse._sparse_mat_vec import sparse_mat_vec


def im_deform_t(Tut, x, n_u, K=None):
    """Adjoint of ``im_deform`` (``Tut`` is the transposed deformation matrix)."""
    if isempty(Tut):
        return x
    n_u = vec(n_u)
    imDim = n_u.size
    x_out = col_reshape(x, n_u)
    if not isempty(K):
        K = col_reshape(K, n_u)
        idfT, dftT = {1: (idf1_conj_trans, dft1_conj_trans), 2: (idf2_conj_trans, dft2_conj_trans),
                      3: (idf3_conj_trans, dft3_conj_trans)}[imDim]
        x_out = dftT(idfT(x_out, n_u, 1.0 / n_u) * K, n_u, 1.0 / n_u)
    x_out = sparse_mat_vec(Tut, x_out, "omp", "complex", False)
    if is_block_shape(x, n_u):
        x_out = block_reshape(x_out, n_u)
    return x_out
