"""Port of src/sparseMat/m/bmSparseMat_matlabSparse2bmSparseMat.m."""

import numpy as np
import scipy.sparse as sp

from monalisa._mat import int32, single
from monalisa.sparseMat.m.bmSparseMat import bmSparseMat


def bmSparseMat_matlabSparse2bmSparseMat(a, N_u, d_u, kernelType, nWin, kernelParam):
    """Convert a (scipy) sparse matrix to a ``bmSparseMat`` of type ``'matlab_ind'``."""
    a = sp.csr_matrix(a, copy=True)
    a.eliminate_zeros()
    a.sort_indices()
    size_1, size_2 = a.shape
    b = bmSparseMat()
    b.r_size = np.int32(size_2)
    b.l_size = np.int32(size_1)
    b.l_nJump = np.int32(size_1)
    b.r_nJump = np.diff(a.indptr).astype(np.int32)[None, :]
    b.r_ind = (a.indices.astype(np.int64) + 1).astype(np.int32)[None, :]
    b.m_val = single(a.data)[None, :]
    b.N_u = int32(N_u)
    b.d_u = single(d_u)
    b.kernel_type = kernelType
    b.nWin = int32(nWin)
    b.kernelParam = single(kernelParam)
    b.block_type = "void"
    b.type = "matlab_ind"
    b.l_squeeze_flag = False
    return b
