"""Port of src/rawDataReader/siemens/dhSiemensReadMetaData.m."""

import numpy as np

from monalisa._mat import squeeze
from monalisa.fourier._idf import idf
from monalisa.io._check_metadata_interactive import check_metadata_interactive
from monalisa.io._correct_metadata_interactive import correct_metadata_interactive
from monalisa.io._mri_acquisition_param import MriAcquisitionParam
from monalisa.io._twix import read_twix

# Header fields probed for the field of view, in MATLAB's order (the last found wins).
_FOV_FIELDS = (
    ("Meas", "ReadFoV"), ("Meas", "FOV"),
    ("Protocol", "ReadFoV"), ("Protocol", "PeFOV"), ("Protocol", "PhaseFoV"),
    ("Config", "ReadFoV"), ("Config", "PhaseFoV"), ("Config", "PeFOV"), ("Config", "RoFOV"),
    ("Dicom", "dPhaseFOV"), ("Dicom", "dReadoutFOV"),
)


def _fov(hdr):
    FoV = np.array([[-1.0, -1.0, -1.0]])
    for sec, key in _FOV_FIELDS:
        val = hdr.get(sec, {}).get(key, None) if hasattr(hdr.get(sec, {}), "get") else None
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            FoV = np.array([[float(val) * 2]])
    return FoV


def _movstd_discard(x, k):
    """MATLAB ``movstd(x, k, 'Endpoints', 'discard')`` for a row vector."""
    w = np.lib.stride_tricks.sliding_window_view(np.ravel(x), k)
    return np.std(w, axis=1, ddof=1).astype(x.dtype)[None, :]


def siemens_read_meta_data(obj, nargout=1):
    """Acquisition parameters of a Siemens file.

    The number of non steady-state shots ``nShot_off`` is estimated from the
    self-navigation signal. When ``obj.autoFlag`` is false, or the FoV is not in
    the header, the parameters are shown for correction (correct_metadata_interactive,
    then check_metadata_interactive with the self-navigation plot); with
    ``autoFlag=True`` set the fields of the returned object in the code instead.
    Returns the parameters, or ``(parameters, reconFoV)`` for ``nargout=2``.
    """
    myTwix = read_twix(obj.argFile)
    img = myTwix.image
    N, nShot, nLine, nEcho = img.NCol, img.NSeg, img.NLin, img.NEco
    nSeg = nLine / nShot
    FoV = _fov(myTwix.hdr)

    node = MriAcquisitionParam(None)
    node.N = np.float64(N)
    node.nLine = np.float64(nLine)
    node.nShot = np.float64(nShot)
    node.nSeg = np.float64(nSeg)
    node.nCh = np.float64(1)
    node.nEcho = np.float64(nEcho)
    node.FoV = FoV
    node.timestamp = img.timestamp
    reconFoV = FoV
    node.nShot_off = np.float64(0)
    node.selfNav_flag = True
    node.roosk_flag = False
    interactive = (not obj.autoFlag) or np.array_equal(np.ravel(reconFoV), [-1, -1, -1])
    if interactive:
        node, reconFoV = correct_metadata_interactive(node, reconFoV)

    if nEcho != 1:
        raise NotImplementedError("siemens_read_meta_data: nEcho > 1, case not implemented yet")
    y_raw = np.transpose(img.unsorted(), (1, 0, 2))
    node.nCh = np.float64(y_raw.shape[0])
    y_raw = np.reshape(y_raw, (int(node.nCh), int(node.N), int(node.nSeg), int(node.nShot)), order="F")

    mySI = squeeze(y_raw[:, :, 0:1, :])
    mySI = idf(mySI, 1, None, 2)
    mySI = squeeze(np.sqrt(np.sum(np.abs(mySI) ** 2, axis=0, keepdims=True)))
    mySI = mySI - np.min(mySI)
    mySI = mySI / np.max(mySI)
    x_SI = np.tile(np.arange(1, mySI.shape[0] + 1, dtype=np.float64)[:, None], (1, mySI.shape[1]))
    prod = (x_SI * mySI).astype(mySI.dtype)  # double .* single -> single
    s_mean = np.mean(prod, axis=0, keepdims=True)
    s_center_mass = np.sum(prod, axis=0, keepdims=True) / np.sum(mySI, axis=0, keepdims=True)
    running_std = _movstd_discard(s_mean, 5)
    threshold = np.percentile(running_std, 15, method="hazen")
    node.nShot_off = np.float64(np.flatnonzero(np.ravel(running_std) < threshold)[0] + 1)
    if interactive:
        node, reconFoV = check_metadata_interactive(mySI, s_mean, s_center_mass, node, reconFoV)
    if nargout >= 2:
        return node, reconFoV
    return node
