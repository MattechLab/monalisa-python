"""Port of src/coilSense/nonCart/bmCoilSense_nonCart_mask_automatic.m."""

import numpy as np

from monalisa._mat import isempty, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.coilSense.automatic.detectROI import detectROI
from monalisa.coilSense.automatic.thresholdRMS_MIP import thresholdRMS_MIP
from monalisa.fourier123.map_function.nonCartesian.bmNasha import bmNasha
from monalisa.imageN.bmMIP import bmMIP
from monalisa.imageN.bmRMS import bmRMS


def bmCoilSense_nonCart_mask_automatic(y, Gn, autoFlag, th_RMS=None, th_MIP=None, borders=None,
                                       open_size=None, close_size=None):
    """Mask of the object for coil sensitivity estimation, from thresholds of
    the RMS and MIP over channels of the gridded images, cut to a bounding box.
    ``autoFlag`` must be true in Python (no interactive selection)."""
    colorMax = 100
    if not autoFlag:
        raise NotImplementedError("Interactive ROI selection is not available in Python; use autoFlag=True")
    N_u = vec(Gn.N_u)
    imDim = N_u.size
    x = bmBlockReshape(bmNasha(y, Gn, N_u), N_u)
    myRMS = bmRMS(x, N_u)
    myMIP = bmMIP(x, N_u)
    myRMS = colorMax * (myRMS - np.min(myRMS)) / np.max(myRMS)
    myMIP = colorMax * (myMIP - np.min(myMIP)) / np.max(myMIP)
    if isempty(th_RMS) or isempty(th_MIP):
        th_RMS, th_MIP = thresholdRMS_MIP(colorMax, myRMS, myMIP, N_u, autoFlag)
    if isempty(borders):
        tempRMS = myRMS.copy()
        tempRMS[tempRMS <= th_RMS] = 0
        tempMIP = myMIP.copy()
        tempMIP[tempMIP <= th_MIP] = 0
        bordersRMS = detectROI(tempRMS, N_u)
        bordersMIP = detectROI(tempMIP, N_u)
        borders = np.concatenate([np.minimum(bordersRMS[:, :1], bordersMIP[:, :1]),
                                  np.maximum(bordersRMS[:, 1:], bordersMIP[:, 1:])], axis=1)
    borders = np.asarray(borders, dtype=np.float64)

    m = (myRMS > th_RMS) & (myMIP > th_MIP)
    if imDim == 3:
        b = borders.astype(np.int64)
        # upstream index arithmetic reproduced, including its asymmetric upper/z bounds
        if b[0, 0] > 1:
            m[: b[0, 0] - 1, :, :] = False
        if b[0, 1] < N_u[0]:
            m[b[0, 1]:, :, :] = False
        if b[1, 0] > 1:
            m[:, : b[1, 0] - 1, :] = False
        if b[1, 1] < N_u[1]:
            m[:, b[1, 1] - 1 :, :] = False
        if b[2, 0] > 1:
            m[:, :, : b[2, 0]] = False
        if b[2, 1] < N_u[2]:
            m[:, :, b[2, 1] - 1 :] = False
    if not isempty(open_size) and open_size > 0:
        raise NotImplementedError("bmCoilSense_nonCart_mask_automatic: open_size is not ported yet")
    if not isempty(close_size) and close_size > 0:
        raise NotImplementedError("bmCoilSense_nonCart_mask_automatic: close_size is not ported yet")
    return bmBlockReshape(m, N_u)
