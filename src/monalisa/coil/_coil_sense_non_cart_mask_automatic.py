"""Port of src/coilSense/nonCart/bmCoilSense_nonCart_mask_automatic.m."""

import numpy as np

from monalisa._mat import isempty, vec
from monalisa.array._block_reshape import block_reshape
from monalisa.coil._detect_roi import detect_roi
from monalisa.coil._select_roi import select_roi
from monalisa.coil._threshold_rms_mip import threshold_rms_mip
from monalisa.image._mip import mip
from monalisa.image._rms import rms
from monalisa.recon._nasha import nasha


def coil_sense_non_cart_mask_automatic(y, Gn, autoFlag, th_RMS=None, th_MIP=None, borders=None,
                                       open_size=None, close_size=None):
    """Mask of the object for coil sensitivity estimation, from thresholds of
    the RMS and MIP over channels of the gridded images, cut to a bounding box.

    With ``autoFlag`` false the thresholds (threshold_rms_mip) and the bounding box (select_roi) are
    chosen in windows, starting from the automatic values, and the RMS, MIP and masked images are
    shown (show_image). The chosen values are printed; passing them as ``th_RMS``, ``th_MIP`` and
    ``borders`` reproduces the mask without windows."""
    colorMax = 100
    N_u = vec(Gn.N_u)
    imDim = N_u.size
    x = block_reshape(nasha(y, Gn, N_u), N_u)
    myRMS = rms(x, N_u)
    myMIP = mip(x, N_u)
    myRMS = colorMax * (myRMS - np.min(myRMS)) / np.max(myRMS)
    myMIP = colorMax * (myMIP - np.min(myMIP)) / np.max(myMIP)
    if isempty(th_RMS) or isempty(th_MIP):
        th_RMS, th_MIP = threshold_rms_mip(colorMax, myRMS, myMIP, N_u, autoFlag)
    if isempty(borders):
        tempRMS = myRMS.copy()
        tempRMS[tempRMS <= th_RMS] = 0
        tempMIP = myMIP.copy()
        tempMIP[tempMIP <= th_MIP] = 0
        bordersRMS = detect_roi(tempRMS, N_u)
        bordersMIP = detect_roi(tempMIP, N_u)
        borders = np.concatenate([np.minimum(bordersRMS[:, :1], bordersMIP[:, :1]),
                                  np.maximum(bordersRMS[:, 1:], bordersMIP[:, 1:])], axis=1)
        if not autoFlag:
            borders = select_roi(tempRMS, tempMIP, N_u, autoFlag, borders)
    borders = np.asarray(borders, dtype=np.float64)
    if not autoFlag:
        from monalisa.display._show_image import show_image

        show_image(myRMS, name="RMS")
        show_image(myMIP, name="MIP")

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
        raise NotImplementedError("coil_sense_non_cart_mask_automatic: open_size is not ported yet")
    if not isempty(close_size) and close_size > 0:
        raise NotImplementedError("coil_sense_non_cart_mask_automatic: close_size is not ported yet")
    if not autoFlag and np.any(~m):
        from monalisa.display._show_image import show_image

        temp_im = m * myRMS
        show_image(np.concatenate([temp_im / np.max(np.abs(temp_im)), m], axis=1), name="mask")
    return block_reshape(m, N_u)
