"""Port of src/rawDataReader/ismrmrd/dhIsmrmrdReadMetaData.m."""

import numpy as np

from monalisa._mat import squeeze
from monalisa.fourierN.bmIDF import bmIDF
from monalisa.mriRecon.class_.bmMriAcquisitionParam import bmMriAcquisitionParam
from monalisa.rawDataReader.checkMetadataInteractive import checkMetadataInteractive
from monalisa.rawDataReader.ismrmrd._mrd import fov, read_mrd, readouts


def _movstd_discard(x, k):
    w = np.lib.stride_tricks.sliding_window_view(np.ravel(x), k)
    return np.std(w, axis=1, ddof=1)[None, :]


def dhIsmrmrdReadMetaData(obj, nargout=1):
    """Acquisition parameters of an ISMRMRD file (counts from the acquisition
    headers, FoV = 2 x encoded FoV of the XML header, ``nShot_off`` estimated
    from the self-navigation signal). Returns the parameters or
    ``(parameters, reconFoV)``. With ``obj.autoFlag`` false the parameters are shown
    for checking (checkMetadataInteractive)."""
    head, data, xml = read_mrd(obj.argFile)
    node = bmMriAcquisitionParam(None)
    node.timestamp = np.asarray(head["acquisition_time_stamp"])[:, None]
    N = np.unique(head["number_of_samples"]).astype(np.float64)
    nCh = np.unique(head["active_channels"]).astype(np.float64)
    if N.size > 1:
        raise ValueError("Different acquisitions have a different number of samples")
    if nCh.size > 1:
        raise ValueError("Different acquisitions have different active channels")
    N, nCh = float(N[0]), float(nCh[0])
    nLine = float(len(data))
    nShot = float(np.unique(head["idx"]["segment"]).size)
    nSeg = nLine / nShot
    node.N = N
    node.nLine = nLine
    node.nShot = nShot
    node.nSeg = nSeg
    node.nCh = nCh
    node.nEcho = float(np.unique(head["idx"]["contrast"]).size)
    node.FoV = (fov(xml, "encodedSpace") * 2)[None, :]
    reconFoV = (fov(xml, "reconSpace") * 2)[None, :]

    y_raw = readouts(data, int(N), int(nCh), int(nLine))
    y_raw = np.transpose(y_raw, (1, 0, 2))
    y_raw = np.reshape(y_raw, (int(nCh), int(N), int(nSeg), int(nShot)), order="F")
    mySI = squeeze(y_raw[:, :, 0:1, :])
    mySI = bmIDF(mySI, 1, None, 2)
    mySI = squeeze(np.sqrt(np.sum(np.abs(mySI) ** 2, axis=0, keepdims=True)))
    mySI = mySI - np.min(mySI)
    mySI = mySI / np.max(mySI)
    x_SI = np.tile(np.arange(1, mySI.shape[0] + 1, dtype=np.float64)[:, None], (1, mySI.shape[1]))
    s_mean = np.mean(x_SI * mySI, axis=0, keepdims=True)
    s_center_mass = np.sum(x_SI * mySI, axis=0, keepdims=True) / np.sum(mySI, axis=0, keepdims=True)
    running_std = _movstd_discard(s_mean, 5)
    threshold = np.percentile(running_std, 15, method="hazen")
    node.nShot_off = float(np.flatnonzero(np.ravel(running_std) < threshold)[0] + 1)
    node.selfNav_flag = True
    node.roosk_flag = False
    if not obj.autoFlag:
        node, reconFoV = checkMetadataInteractive(mySI, s_mean, s_center_mass, node, reconFoV)
    return (node, reconFoV) if nargout >= 2 else node
