"""Numba ports of the MEX kernels bmGridder_n2u_leight{1,2,3}_mex.cpp.

The loops, their order and the float32 arithmetic follow the C++ sources so
that results agree with MATLAB to rounding level. The C++ code uses a
Gaussian kernel whatever the kernel type passed to the MATLAB wrapper.
"""

import math

import numba
import numpy as np

_F32 = np.float32


@numba.njit(cache=True)
def _setup(nWin, kernelParam_1):
    if nWin % 2 > 0:
        t_shift = _F32(0.5)
        nWin_half = (nWin - 1) // 2
    else:
        t_shift = _F32(0.0)
        nWin_half = nWin // 2 - 1
    mySigma = _F32(kernelParam_1)
    g1 = _F32(1.0) / (_F32(math.sqrt(2 * 3.141592)) * mySigma)
    g2 = _F32(-1.0) / (_F32(2.0) * (mySigma * mySigma))
    return t_shift, nWin_half, g1, g2


@numba.njit(cache=True)
def _normalize(bRe, bIm, normalize):
    nCh = bRe.shape[0]
    for i in range(normalize.size):
        val = normalize[i]
        if val < 1e-5:
            val = _F32(1.0)
        for k in range(nCh):
            bRe[k, i] /= val
            bIm[k, i] /= val


@numba.njit(cache=True)
def bmGridder_n2u_leight3_mex(aRe, aIm, tx, ty, tz, Dn, Nx, Ny, Nz, nWin, kernelParam_1):
    """3D: ``a`` is ``[nCh, nPt]`` (float32), returns ``(bRe, bIm)`` of shape ``[nCh, Nx*Ny*Nz]``."""
    nCh, nPt = aRe.shape
    Nu_tot = Nx * Ny * Nz
    bRe = np.zeros((nCh, Nu_tot), dtype=np.float32)
    bIm = np.zeros((nCh, Nu_tot), dtype=np.float32)
    normalize = np.zeros(Nu_tot, dtype=np.float32)
    t_shift, nWin_half, g1, g2 = _setup(nWin, kernelParam_1)
    nWin_half_f = _F32(nWin_half)
    one = _F32(1.0)
    for i in range(nPt):
        cx_f = _F32(math.trunc(tx[i] + t_shift))
        cy_f = _F32(math.trunc(ty[i] + t_shift))
        cz_f = _F32(math.trunc(tz[i] + t_shift))
        rx = tx[i] - cx_f
        ry = ty[i] - cy_f
        rz = tz[i] - cz_f
        cx = int(cx_f) - 1
        cy = int(cy_f) - 1
        cz = int(cz_f) - 1
        dn = Dn[i]
        nz = cz - nWin_half
        uz = -nWin_half_f
        for _z in range(nWin):
            if nz < 0 or nz > Nz - 1:
                nz += 1
                uz += one
                continue
            ny = cy - nWin_half
            uy = -nWin_half_f
            for _y in range(nWin):
                if ny < 0 or ny > Ny - 1:
                    ny += 1
                    uy += one
                    continue
                nx = cx - nWin_half
                ux = -nWin_half_f
                for _x in range(nWin):
                    if nx < 0 or nx > Nx - 1:
                        nx += 1
                        ux += one
                        continue
                    dx = rx - ux
                    dy = ry - uy
                    dz = rz - uz
                    d_square = dx * dx + dy * dy + dz * dz
                    w = g1 * np.exp(g2 * d_square) * dn
                    idx = nx + ny * Nx + nz * Nx * Ny
                    normalize[idx] += w
                    for ch in range(nCh):
                        bRe[ch, idx] += w * aRe[ch, i]
                        bIm[ch, idx] += w * aIm[ch, i]
                    nx += 1
                    ux += one
                ny += 1
                uy += one
            nz += 1
            uz += one
    _normalize(bRe, bIm, normalize)
    return bRe, bIm


@numba.njit(cache=True)
def bmGridder_n2u_leight2_mex(aRe, aIm, tx, ty, Dn, Nx, Ny, nWin, kernelParam_1):
    """2D version of :func:`bmGridder_n2u_leight3_mex`."""
    nCh, nPt = aRe.shape
    Nu_tot = Nx * Ny
    bRe = np.zeros((nCh, Nu_tot), dtype=np.float32)
    bIm = np.zeros((nCh, Nu_tot), dtype=np.float32)
    normalize = np.zeros(Nu_tot, dtype=np.float32)
    t_shift, nWin_half, g1, g2 = _setup(nWin, kernelParam_1)
    nWin_half_f = _F32(nWin_half)
    one = _F32(1.0)
    for i in range(nPt):
        cx_f = _F32(math.trunc(tx[i] + t_shift))
        cy_f = _F32(math.trunc(ty[i] + t_shift))
        rx = tx[i] - cx_f
        ry = ty[i] - cy_f
        cx = int(cx_f) - 1
        cy = int(cy_f) - 1
        dn = Dn[i]
        ny = cy - nWin_half
        uy = -nWin_half_f
        for _y in range(nWin):
            if ny < 0 or ny > Ny - 1:
                ny += 1
                uy += one
                continue
            nx = cx - nWin_half
            ux = -nWin_half_f
            for _x in range(nWin):
                if nx < 0 or nx > Nx - 1:
                    nx += 1
                    ux += one
                    continue
                dx = rx - ux
                dy = ry - uy
                d_square = dx * dx + dy * dy
                w = g1 * np.exp(g2 * d_square) * dn
                idx = nx + ny * Nx
                normalize[idx] += w
                for ch in range(nCh):
                    bRe[ch, idx] += w * aRe[ch, i]
                    bIm[ch, idx] += w * aIm[ch, i]
                nx += 1
                ux += one
            ny += 1
            uy += one
    _normalize(bRe, bIm, normalize)
    return bRe, bIm


@numba.njit(cache=True)
def bmGridder_n2u_leight1_mex(aRe, aIm, tx, Dn, Nx, nWin, kernelParam_1):
    """1D version of :func:`bmGridder_n2u_leight3_mex`."""
    nCh, nPt = aRe.shape
    bRe = np.zeros((nCh, Nx), dtype=np.float32)
    bIm = np.zeros((nCh, Nx), dtype=np.float32)
    normalize = np.zeros(Nx, dtype=np.float32)
    t_shift, nWin_half, g1, g2 = _setup(nWin, kernelParam_1)
    nWin_half_f = _F32(nWin_half)
    one = _F32(1.0)
    for i in range(nPt):
        cx_f = _F32(math.trunc(tx[i] + t_shift))
        rx = tx[i] - cx_f
        cx = int(cx_f) - 1
        dn = Dn[i]
        nx = cx - nWin_half
        ux = -nWin_half_f
        for _x in range(nWin):
            if nx < 0 or nx > Nx - 1:
                nx += 1
                ux += one
                continue
            dx = rx - ux
            d_square = dx * dx
            w = g1 * np.exp(g2 * d_square) * dn
            normalize[nx] += w
            for ch in range(nCh):
                bRe[ch, nx] += w * aRe[ch, i]
                bIm[ch, nx] += w * aIm[ch, i]
            nx += 1
            ux += one
    _normalize(bRe, bIm, normalize)
    return bRe, bIm
