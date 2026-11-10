"""Port of src/image123/bmImDeform.m."""


from monalisa._mat import isempty, vec
from monalisa.array._block_reshape import block_reshape
from monalisa.array._col_reshape import col_reshape
from monalisa.array._is_block_shape import is_block_shape
from monalisa.fourier._dft1 import dft1
from monalisa.fourier._dft2 import dft2
from monalisa.fourier._dft3 import dft3
from monalisa.fourier._idf1 import idf1
from monalisa.fourier._idf2 import idf2
from monalisa.fourier._idf3 import idf3
from monalisa.sparse._sparse_mat_vec import sparse_mat_vec


def im_deform(Tu, x, n_u, K=None):
    """Apply the deformation matrix ``Tu`` to the images ``x`` (identity when ``Tu``
    is empty); with ``K`` the deformed images are filtered in k-space."""
    if isempty(Tu):
        return x
    n_u = vec(n_u)
    imDim = n_u.size
    x_out = sparse_mat_vec(Tu, col_reshape(x, n_u), "omp", "complex", False)
    if not isempty(K):
        K = col_reshape(K, n_u)
        dft, idf = {1: (dft1, idf1), 2: (dft2, idf2), 3: (dft3, idf3)}[imDim]
        x_out = idf(dft(x_out, n_u, 1.0 / n_u) * K, n_u, 1.0 / n_u)
    if is_block_shape(x, n_u):
        x_out = block_reshape(x_out, n_u)
    return x_out
