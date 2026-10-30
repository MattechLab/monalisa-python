"""Port of src/mriRecon/function/bmLowRes.m."""

import numpy as np

from monalisa._mat import vec
from monalisa.arrayUtility.bmPointReshape import bmPointReshape


def bmLowRes(c, t, ve, N_u, dK_u, nargout=3):
    """Keep the samples whose trajectory lies in the box of ``N_u`` grid steps ``dK_u``.

    Returns ``(c, t, ve)`` restricted to these points (truncated to ``nargout``).
    """
    myEps = np.finfo(np.float64).eps * 1e3
    N_u = vec(N_u)
    dK_u = vec(dK_u)
    t = np.asarray(bmPointReshape(t))
    c = np.asarray(bmPointReshape(c))
    ve = np.asarray(bmPointReshape(ve))
    myMask = np.ones(t.shape[1], dtype=bool)
    for d in range(N_u.size):
        L = dK_u[d] * N_u[d]
        myMask &= (-L / 2 - myEps <= t[d, :]) & (t[d, :] <= L / 2 - dK_u[d] + myEps)
    out = (c[:, myMask], t[:, myMask], ve[:, myMask])
    return out[0] if nargout <= 1 else out[:nargout]
