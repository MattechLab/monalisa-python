"""Port of src/gridding123/m/bmImDeformField2sparseMat_ind_weight.m."""

import numpy as np

from monalisa._mat import isempty, vec
from monalisa.array._point_reshape import point_reshape
from monalisa.sparse._sparse_mat_r_n_jump_to_index import sparse_mat_r_n_jump_to_index


def im_deform_field_to_sparse_mat_ind_weight(v, N_u, Dn, torus_flag):
    """Grid indices (``ind_1``), point indices (``ind_2``, both 1-based doubles)
    and bump-kernel weights of the interpolation at the displaced pixel positions
    ``x + v``; returns ``(ind_1, ind_2, myWeight, Dn)`` as columns."""
    v = np.asarray(point_reshape(v), dtype=np.float64)
    Dn = None if isempty(Dn) else np.ravel(np.asarray(Dn, dtype=np.float64), order="F")
    N_u = vec(N_u)
    imDim, nPt = v.shape
    if nPt != np.prod(N_u):
        raise ValueError("In bmImDeformField_Gn_Gu_Gut : the deformation field must have as many vectors as "
                         "the number of pixel(voxel) in the image. ")
    N = [int(n) for n in N_u[:imDim]]
    grids = np.meshgrid(*[np.arange(1, n + 1) for n in N], indexing="ij")
    t = np.stack([g.ravel(order="F") for g in grids]).astype(np.float64) + v
    deleteMask = np.zeros(nPt, dtype=bool)
    for d in range(imDim):
        deleteMask |= (t[d] < 1) | (t[d] > N[d])
    cg = np.meshgrid(*([np.arange(2)] * imDim), indexing="ij")
    c = np.stack([g.ravel(order="F") for g in cg]).astype(np.float64)  # (imDim, nNb)
    nNb = c.shape[1]
    t_floor = np.floor(t)
    t_rest = t - t_floor
    dd = t_rest[:, None, :] - c[:, :, None]  # (imDim, nNb, nPt)
    sq = 0
    for i in range(imDim):
        sq = sq + dd[i] ** 2
    d = np.sqrt(sq)
    with np.errstate(divide="ignore", over="ignore"):
        w = np.exp(-1.0 / (1 - d**2))
    w[np.isinf(w)] = 0
    w = w * (np.abs(d) < 1).astype(np.float64)
    n = t_floor[:, None, :] + c[:, :, None]
    lin = np.zeros((nNb, nPt))
    stride = 1
    for i in range(imDim):
        lin = lin + (np.mod(n[i] - 1, N[i])) * stride
        stride *= N[i]
    lin = lin + 1
    myOne = np.ones(nPt)
    if Dn is not None:
        Dn = np.tile(Dn[None, :], (nNb, 1))
    if not torus_flag:
        keep = ~deleteMask
        lin, w = lin[:, keep], w[:, keep]
        myOne[deleteMask] = 0
        if Dn is not None:
            Dn = Dn[:, keep]
    ind_1 = np.reshape(lin, (-1, 1), order="F")
    ind_2 = sparse_mat_r_n_jump_to_index(nNb * myOne).astype(np.float64).T
    myWeight = np.reshape(w, (-1, 1), order="F")
    Dn = np.zeros((0, 1)) if Dn is None else np.reshape(Dn, (-1, 1), order="F")
    return ind_1, ind_2, myWeight, Dn
