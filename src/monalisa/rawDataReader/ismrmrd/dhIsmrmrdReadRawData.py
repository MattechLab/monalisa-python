"""Port of src/rawDataReader/ismrmrd/dhIsmrmrdReadRawData.m."""

import numpy as np

from monalisa._mat import scalar
from monalisa.rawDataReader.ismrmrd._mrd import read_mrd, readouts


def dhIsmrmrdReadRawData(obj, flagSS, flagExcludeSI):
    """Readouts ``[nCh, N, nSeg*nShot]`` (single) of an ISMRMRD file, optionally
    without the non steady-state shots and the self-navigation segment."""
    p = obj.acquisitionParams
    nCh, N, nSeg, nShot, nLine = (int(scalar(v)) for v in (p.nCh, p.N, p.nSeg, p.nShot, p.nLine))
    nEcho, nShot_off = int(scalar(p.nEcho)), int(scalar(p.nShot_off))
    _, data, _ = read_mrd(obj.argFile)
    r = readouts(data, N, nCh, nLine).astype(np.complex64)
    if nEcho == 1:
        r = np.transpose(r, (1, 0, 2))
        r = np.reshape(r, (nCh, N, nSeg, nShot), order="F")
        if flagSS and nShot_off > 0:
            r = r[:, :, :, nShot_off:]
            nShot -= nShot_off
        if flagExcludeSI:
            r = r[:, :, 1:, :]
            nSeg -= 1
        return np.reshape(r, (nCh, N, nSeg * nShot), order="F")
    if nEcho == 2:
        raise NotImplementedError("bmTwix_data : nEcho == 2, case not implemented, yet.")
    raise NotImplementedError("bmTwix_data : case not implemented. ")
