"""Port of src/gridding123/m/bmTraj2SparseMat.m."""

import numba
import numpy as np
import scipy.sparse as sp
import scipy.special

from monalisa._mat import cell_from_items, cell_items, cell_shape, double, iscell, single, vec
from monalisa.array._point_reshape import point_reshape
from monalisa.sparse._sparse_mat_from_matlab_sparse import sparse_mat_from_matlab_sparse
from monalisa.util._default_kernel import default_kernel
from monalisa.util._default_sparse_type import default_sparse_type

_CHUNK = 1 << 18


@numba.njit(cache=True)
def _neighbors(t, c, floor_shift, N, d_out, n_out):
    """Distance to and 0-based linear grid index of each kernel neighbor.

    ``t`` ``[imDim, nPt]`` (grid units, shifted), ``c`` ``[imDim, nNb]`` offsets.
    Mirrors MATLAB: ``t_floor = floor(t + shift)``, ``d = sqrt(sum((t - t_floor - c).^2))``,
    ``n = mod(t_floor + c - 1, N) + 1``.
    """
    imDim, nPt = t.shape
    nNb = c.shape[1]
    for p in range(nPt):
        for j in range(nNb):
            sq = 0.0
            lin = 0
            stride = 1
            for i in range(imDim):
                tf = np.floor(t[i, p] + floor_shift[i])
                di = (t[i, p] - tf) - c[i, j]
                sq = sq + di * di
                ni = int(tf + c[i, j])
                ni = (ni - 1) % N[i]
                lin += ni * stride
                stride *= N[i]
            d_out[j, p] = np.sqrt(sq)
            n_out[j, p] = lin


def _kernel_weight(d, kernelType, kernelParam):
    if kernelType == "gauss":
        mySigma = kernelParam[0]
        return np.exp(-0.5 * ((d - 0) / mySigma) ** 2) / (np.sqrt(2 * np.pi) * mySigma)
    if kernelType == "kaiser":
        myTau, myAlpha = kernelParam[0], kernelParam[1]
        I0myAlpha = scipy.special.i0(myAlpha)
        w = np.maximum(1 - (d / myTau) ** 2, 0)
        w = myAlpha * np.sqrt(w)
        return scipy.special.i0(w) / I0myAlpha
    raise ValueError(f"Unknown kernelType {kernelType!r}")


@numba.njit(cache=True)
def _row_sums(indptr, data):
    out = np.zeros(indptr.size - 1)
    for i in range(out.size):
        s = 0.0
        for p in range(indptr[i], indptr[i + 1]):
            s += data[p]
        out[i] = s
    return out


def _row_normalize(m):
    """``diag(1 ./ sum(m, 2)) * m`` for the rows with a non-zero sum (MATLAB order)."""
    m = sp.csr_matrix(m)
    m.sum_duplicates()
    m.sort_indices()
    sums = _row_sums(m.indptr, m.data)
    counts = np.diff(m.indptr)
    scale = np.zeros_like(sums)
    nz = sums != 0
    scale[nz] = 1.0 / sums[nz]
    m.data = np.repeat(scale, counts) * m.data
    m.eliminate_zeros()
    return m


def traj_to_sparse_mat(t, v, N_u, dK_u, sparseType=None, kernelType=None, nWin=None, kernelParam=None,
                       *, nargout=3):
    """Gridding matrices of the trajectory ``t`` with volume elements ``v``.

    ``nargout`` selects the outputs as in MATLAB: ``Gn`` (1), ``(Gu, Gut)``
    (2) or ``(Gn, Gu, Gut)`` (3). ``Gn`` (``[prod(N_u), nPt]``) grids
    density-compensated data onto the Cartesian grid, ``Gu`` (``[nPt,
    prod(N_u)]``) interpolates the grid at the trajectory points and ``Gut``
    is its transpose. Cells of trajectories give cells of matrices.
    """
    if iscell(t):
        if nargout not in (1, 2, 3):
            raise ValueError("wrong list of arguments. ")
        res = [traj_to_sparse_mat(ti, vi, N_u, dK_u, sparseType, kernelType, nWin, kernelParam, nargout=nargout)
               for ti, vi in zip(cell_items(t), cell_items(v), strict=True)]
        shape = cell_shape(t)
        if nargout == 1:
            return cell_from_items(res, shape)
        return tuple(cell_from_items([r[k] for r in res], shape) for k in range(nargout))

    kernelType, nWin, kernelParam = default_kernel(kernelType, nWin, kernelParam)
    sparseType = default_sparse_type(sparseType)
    t = double(point_reshape(t)).copy()
    Dn = double(v).ravel(order="F").copy()
    N_u = double(single(vec(N_u)))
    dK_u = double(single(vec(dK_u)))
    nWin = double(single(vec(nWin)))
    kernelParam = double(single(vec(kernelParam)))
    imDim, nPt = t.shape
    if sparseType != "bmSparseMat":
        raise ValueError("The given sparseType is not recognized")

    Nu_tot = 1.0
    Du = 1.0
    for d in range(imDim):
        Nu_tot = Nu_tot * N_u[d]
        t[d, :] = t[d, :] / dK_u[d]
        Dn = Dn / dK_u[d]
        FoV_d = 1 / dK_u[d]
        Du = Du * (FoV_d / N_u[d])
    shift = np.trunc(N_u[:imDim] / 2 + 1)
    t = t + shift[:, None]
    deleteMask = np.zeros(nPt, dtype=bool)
    for d in range(imDim):
        deleteMask |= (t[d, :] < 1) | (t[d, :] > N_u[d])

    w = int(nWin[0])
    if w % 2 == 0:
        rng = np.arange(-w / 2 - 1, w / 2 + 1)
        floor_shift = np.zeros(imDim)
    else:
        rng = np.arange(-(w // 2), w // 2 + 1, dtype=np.float64)
        floor_shift = np.full(imDim, 0.5)
    grids = np.meshgrid(*([rng] * imDim), indexing="ij")
    c = np.stack([g.ravel(order="F") for g in grids]).astype(np.float64)
    nNb = c.shape[1]

    keep = np.flatnonzero(~deleteMask)
    tk = np.ascontiguousarray(t[:, keep])
    Nk = len(keep)
    N_int = N_u[:imDim].astype(np.int64)
    weights = np.empty((nNb, Nk))
    grid_idx = np.empty((nNb, Nk), dtype=np.int64)
    for s in range(0, Nk, _CHUNK):
        e = min(s + _CHUNK, Nk)
        dist = np.empty((nNb, e - s))
        idx = np.empty((nNb, e - s), dtype=np.int64)
        _neighbors(tk[:, s:e], c, floor_shift, N_int, dist, idx)
        weights[:, s:e] = _kernel_weight(dist, kernelType, kernelParam)
        grid_idx[:, s:e] = idx
    point_idx = np.repeat(keep, nNb)
    grid_flat = grid_idx.ravel(order="F")
    w_flat = weights.ravel(order="F")
    Nu_tot = int(Nu_tot)

    def to_bm(m):
        return sparse_mat_from_matlab_sparse(m, N_u[None, :], dK_u[None, :], kernelType, nWin,
                                             kernelParam[None, :])

    out = {}
    if nargout in (1, 3):
        Dn_flat = np.repeat(Dn[keep], nNb)
        m = sp.coo_matrix((w_flat * Dn_flat, (grid_flat, point_idx)), shape=(Nu_tot, nPt))
        Gn = to_bm(_row_normalize(m))
        Gn.l_squeeze()
        Gn.cpp_prepare("one_block", None, None)
        out["Gn"] = Gn
    if nargout in (2, 3):
        m = _row_normalize(sp.coo_matrix((w_flat * Du, (point_idx, grid_flat)), shape=(nPt, Nu_tot)))
        Gu = to_bm(m)
        Gut = to_bm(m.T)
        Gu.cpp_prepare("one_block", None, None)
        Gut.l_squeeze()
        Gut.cpp_prepare("one_block", None, None)
        out["Gu"], out["Gut"] = Gu, Gut
    if nargout == 1:
        return out["Gn"]
    if nargout == 2:
        return out["Gu"], out["Gut"]
    return out["Gn"], out["Gu"], out["Gut"]
