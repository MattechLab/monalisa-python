"""Port of src/sparseMat/m/bmSparseMat_vec.m."""

import numpy as np

from monalisa._mat import disp, isempty
from monalisa.sparse._sparse_vec import matvec, zeros


def _matvec(s, V):
    row_of, row_start, cols, vals = s.csr()
    W = zeros((int(s.l_size), V.shape[1]), np.float32)
    matvec(row_of, row_start, cols, vals, np.asarray(V, dtype=np.float32), W)
    return W


def _matvec_complex(s, V):
    row_of, row_start, cols, vals = s.csr()
    W = zeros((int(s.l_size), V.shape[1]), np.complex64)
    matvec(row_of, row_start, cols, vals, V, W)
    return W


def sparse_mat_vec(s, v, *varargin):
    """Product of the ``SparseMat`` ``s`` with the vectors ``v`` (single).

    ``varargin``: ``omp_flag`` (``'omp'`` or bool), ``'complex'`` / ``'real'``,
    and the transpose flag ``T`` (vectors are the rows of ``v``; by default
    guessed from the shape as in MATLAB). Returns ``[l_size, n_vec]`` (or
    ``[n_vec, l_size]`` in row mode), single.
    """
    if s is None or isempty(v):
        return None
    s.check()
    v = np.asarray(v)
    if v.ndim > 2:
        raise ValueError("The input list of vectors 'v' is a matrix that cannot have more that 2 dim. ")
    if v.dtype not in (np.float32, np.complex64):
        raise TypeError("The class SparseMat is for single class only. ")
    if s.block_type not in ("one_block", "multi_block"):
        raise ValueError("The SparseMat is not cpp_prepared. ")
    if not s.check_flag:
        raise ValueError("The SparseMat has check_flag to false. ")
    if v.ndim == 1:
        v = v[:, None]

    omp_flag = False
    if len(varargin) > 0:
        if isinstance(varargin[0], str):
            omp_flag = varargin[0] == "omp"
        elif isinstance(varargin[0], (bool, np.bool_)):
            omp_flag = bool(varargin[0])
    R_flag = True
    if len(varargin) > 1:
        if varargin[1] == "complex":
            R_flag = False
        elif varargin[1] == "real":
            R_flag = True
    if len(varargin) > 2 and varargin[2] is not None:
        T_flag = bool(varargin[2]) or varargin[2] == "T"
    else:
        T_flag = not (v.shape[0] >= v.shape[1])
    one_block = s.block_type == "one_block"

    if T_flag:
        V = v.T
        if R_flag and one_block and omp_flag:
            raise NotImplementedError("Case not implemented.")
        if R_flag and not one_block and not omp_flag:
            raise NotImplementedError("Case not implemented.")
        if not R_flag and not one_block and not omp_flag:
            raise NotImplementedError("Case not implemented")
        if not R_flag and one_block and omp_flag:
            raise NotImplementedError("Case not implemented.")
        name = {(True, True): "rR_oBlock", (True, False): "rR_nBlock_omp",
                (False, True): "cR_oBlock", (False, False): "cR_nBlock_omp"}[(R_flag, one_block)]
        disp(f"bmSparseMat_{name}_mex")
    else:
        V = v
        if not one_block:
            raise NotImplementedError("Case not implemented")
        if R_flag:
            disp("bmSparseMat_rC_oBlock_omp_mex" if omp_flag else "bmSparseMat_rC_oBlock_mex")

    if R_flag:
        W = _matvec(s, np.real(V))
    elif V.dtype == np.complex64:
        W = _matvec_complex(s, V)  # same values as the two real products below, without copies
    else:
        W = _matvec(s, np.real(V)) + 1j * _matvec(s, np.imag(V)).astype(np.complex64)
        W = W.astype(np.complex64)
    return W.T if T_flag else W
