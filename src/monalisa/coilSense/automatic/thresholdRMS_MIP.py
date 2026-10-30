"""Port of src/coilSense/automatic/thresholdRMS_MIP.m (automatic mode)."""

import numpy as np
from scipy.optimize import brentq

from monalisa._mat import mround, single
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape


def _normpdf(x, mu, sigma):
    return np.exp(-0.5 * ((x - mu) / sigma) ** 2) / (np.sqrt(2 * np.pi) * sigma)


def _fit_gmm2(data, max_iter=1000, tol=1e-12):
    """Two-component 1D Gaussian mixture by EM (deterministic quantile start).

    MATLAB's ``fitgmdist`` starts from random k-means++ seeds; both converge
    to the same maximum-likelihood fit on the bimodal intensity histograms
    used here, and the threshold is rounded to an integer afterwards.
    """
    x = np.asarray(data, dtype=np.float64).ravel()
    mu = np.quantile(x, [0.25, 0.75])
    var = np.full(2, x.var())
    w = np.array([0.5, 0.5])
    ll_old = -np.inf
    for _ in range(max_iter):
        p = w * _normpdf(x[:, None], mu, np.sqrt(var))
        tot = p.sum(axis=1, keepdims=True)
        ll = np.log(tot).sum()
        r = p / tot
        nk = r.sum(axis=0)
        w = nk / x.size
        mu = (r * x[:, None]).sum(axis=0) / nk
        var = (r * (x[:, None] - mu) ** 2).sum(axis=0) / nk
        if abs(ll - ll_old) <= tol * abs(ll):
            break
        ll_old = ll
    return mu, np.sqrt(var), w


def _fzero(f, x0):
    """MATLAB ``fzero`` with a scalar start: expanding symmetric search, then Brent."""
    fx = f(x0)
    if fx == 0:
        return x0
    dx = x0 / 50 if x0 != 0 else 1 / 50
    a = b = x0
    fa = fb = fx
    while (fa > 0) == (fb > 0):
        dx = np.sqrt(2) * dx
        a = x0 - dx
        fa = f(a)
        if (fa > 0) != (fb > 0):
            break
        b = x0 + dx
        fb = f(b)
    lo, hi = (a, b) if a < b else (b, a)
    return brentq(f, lo, hi, xtol=np.finfo(float).eps * max(1.0, abs(x0)), maxiter=500)


def _detectThreshold_GMM2(data):
    mu, sigma, w = _fit_gmm2(data)

    def diff_pdf(x):
        return _normpdf(x, mu[0], sigma[0]) * w[0] - _normpdf(x, mu[1], sigma[1]) * w[1]

    return np.float32(mround(_fzero(diff_pdf, (mu[0] + mu[1]) / 2)))


def thresholdRMS_MIP(colorMax, dataRMS, dataMIP, N_u, autoFlag):
    """Thresholds ``(thRMS, thMIP)`` separating background from object in the
    RMS and MIP images (crossing of a two-Gaussian fit of their histograms).
    Only the automatic mode exists in Python."""
    dataRMS = single(bmBlockReshape(dataRMS, N_u))
    dataMIP = single(bmBlockReshape(dataMIP, N_u))
    thRMS = _detectThreshold_GMM2(dataRMS)
    thMIP = _detectThreshold_GMM2(dataMIP)
    if not autoFlag:
        raise NotImplementedError(
            "Interactive threshold selection is not available in Python; use autoFlag=True"
        )
    return thRMS, thMIP
