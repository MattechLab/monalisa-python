"""Port of src/gridding123/m/bmImDeformField2SparseMat.m."""

import numpy as np
import scipy.sparse as sp

from monalisa._mat import cell_from_items, cell_items, cell_shape, iscell, isempty, vec
from monalisa.gridding123.m.bmImDeformField2sparseMat_ind_weight import bmImDeformField2sparseMat_ind_weight
from monalisa.gridding123.m.bmTraj2SparseMat import _row_normalize
from monalisa.sparseMat.m.bmSparseMat_matlabSparse2bmSparseMat import bmSparseMat_matlabSparse2bmSparseMat


def bmImDeformField2SparseMat(v, N_u, Dn=None, torus_flag=None, *, nargout=2):
    """Sparse interpolation matrices of the deformation field ``v``: ``Gn``
    (``nargout`` 1), ``(Gu, Gut)`` (2) or ``(Gn, Gu, Gut)`` (3). ``Gu`` warps an
    image (column format) by ``v``; ``Gut`` is its transpose."""
    if iscell(v):
        vs = cell_items(v)
        Dns = [None] * len(vs) if isempty(Dn) else cell_items(Dn)
        res = [bmImDeformField2SparseMat(vi, N_u, di, torus_flag, nargout=nargout)
               for vi, di in zip(vs, Dns, strict=True)]
        shape = cell_shape(v)
        if nargout == 1:
            return cell_from_items(res, shape)
        return tuple(cell_from_items([r[k] for r in res], shape) for k in range(nargout))
    if isempty(v):
        return (None,) * nargout if nargout > 1 else None
    torus_flag = False if isempty(torus_flag) else bool(torus_flag)
    N_u = vec(N_u)
    Nu_tot = int(np.prod(N_u))
    v = np.asarray(v)
    nPt = int(np.size(v) // N_u.size) if v.size else 0
    if nPt != Nu_tot:
        raise ValueError("In bmImDeformField2SparseMat : the deformation field must have as many vectors as "
                         "the number of pixel(voxel) in the image. ")
    ind_1, ind_2, w, Dn = bmImDeformField2sparseMat_ind_weight(v, N_u, Dn, torus_flag)
    rows = ind_2.ravel().astype(np.int64) - 1
    cols = ind_1.ravel().astype(np.int64) - 1
    w = w.ravel()

    def to_bm(m):
        return bmSparseMat_matlabSparse2bmSparseMat(m, N_u[None, :], np.array([[1.0, 1.0, 1.0]]), "bump", 2.0,
                                                    None)

    out = {}
    if nargout in (1, 3):
        if Dn.size == 0:
            raise ValueError("Dn is required for Gn")
        m = sp.coo_matrix((w * Dn.ravel(), (cols, rows)), shape=(Nu_tot, nPt))
        out["Gn"] = to_bm(_row_normalize(m))
        out["Gn"].cpp_prepare("one_block", None, None)
    if nargout in (2, 3):
        m = _row_normalize(sp.coo_matrix((w, (rows, cols)), shape=(nPt, Nu_tot)))
        Gu, Gut = to_bm(m), to_bm(m.T)
        Gu.cpp_prepare("one_block", None, None)
        Gut.cpp_prepare("one_block", None, None)
        out["Gu"], out["Gut"] = Gu, Gut
    if nargout == 1:
        return out["Gn"]
    if nargout == 2:
        return out["Gu"], out["Gut"]
    return out["Gn"], out["Gu"], out["Gut"]
