"""Properties of the non-Cartesian operators that hold independently of MATLAB."""

import numpy as np
import pytest
import scipy.sparse as sp

import monalisa as ml


def _radial_2d(N=64, nLine=48, N_u=(64, 64), FoV=240.0):
    dK = 1.0 / FoV
    r = (np.arange(N) - N / 2) * dK
    phi = np.pi * np.arange(nLine) / nLine
    t = np.stack([np.outer(r, np.cos(phi)), np.outer(r, np.sin(phi))])  # (2, N, nLine)
    return t.reshape(2, N, nLine), np.array([N_u], dtype=float), np.array([[dK, dK]])


@pytest.fixture(scope="module")
def setup():
    t, N_u, dK_u = _radial_2d()
    ve = ml.bmVolumeElement(t, "voronoi_full_radial2")
    Gn, Gu, Gut = ml.bmTraj2SparseMat(t, ve, N_u, dK_u)
    return t, ve, N_u, dK_u, Gn, Gu, Gut


def _to_scipy(G):
    row_of, row_start, cols, vals = G.csr()
    rows = np.repeat(row_of, np.diff(row_start))
    return sp.csr_matrix((vals.astype(np.float64), (rows, cols)), shape=(int(G.l_size), int(G.r_size)))


def test_sparse_vec_matches_scipy(setup):
    *_, Gn, Gu, Gut = setup
    rng = np.random.default_rng(0)
    for G in (Gn, Gu, Gut):
        v = (rng.standard_normal((int(G.r_size), 3)) + 1j * rng.standard_normal((int(G.r_size), 3)))
        v = v.astype(np.complex64)
        w = ml.bmSparseMat_vec(G, v, "omp", "complex", False)
        ref = _to_scipy(G) @ v.astype(np.complex128)
        assert w.dtype == np.complex64
        assert np.linalg.norm(w - ref) / np.linalg.norm(ref) < 1e-6
        wt = ml.bmSparseMat_vec(G, np.ascontiguousarray(v.T), False, "complex", True)
        np.testing.assert_array_equal(wt, w.T)


def test_gut_is_transpose_of_gu(setup):
    *_, Gu, Gut = setup
    assert abs(_to_scipy(Gu).T - _to_scipy(Gut)).max() == 0


def test_shanna_nakatsha_adjoint(setup):
    _, _, N_u, dK_u, _, Gu, Gut = setup
    nCh = 4
    rng = np.random.default_rng(1)
    n = int(np.prod(N_u))
    C = (rng.standard_normal((n, nCh)) + 1j * rng.standard_normal((n, nCh))).astype(np.complex64)
    KFC = ml.bmKF(C, N_u, N_u, dK_u, nCh)
    KFC_conj = ml.bmKF_conj(np.conj(C), N_u, N_u, dK_u, nCh)
    x = (rng.standard_normal((n, 1)) + 1j * rng.standard_normal((n, 1))).astype(np.complex64)
    y = (rng.standard_normal((int(Gu.l_size), nCh)) + 1j * rng.standard_normal((int(Gu.l_size), nCh)))
    y = y.astype(np.complex64)
    Ax = ml.bmShanna(x, Gu, KFC, N_u, "MATLAB")
    Aty = ml.bmNakatsha(y, Gut, KFC_conj, True, N_u, "MATLAB")
    lhs = np.vdot(y.astype(np.complex128), Ax.astype(np.complex128))
    rhs = np.vdot(Aty.astype(np.complex128), x.astype(np.complex128))
    assert abs(lhs - rhs) / abs(lhs) < 1e-5


def test_complex_row_mode_with_omp_is_not_implemented(setup):
    """Like MATLAB: complex row-vector products with one block have no OpenMP variant."""
    *_, Gu, _ = setup
    v = np.ones((2, int(Gu.r_size)), dtype=np.complex64)
    with pytest.raises(NotImplementedError):
        ml.bmSparseMat_vec(Gu, v, "omp", "complex", True)
