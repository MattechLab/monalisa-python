"""Port of src/rawDataReader/siemens/bmSiemensReadRawData.m."""

import numpy as np

from monalisa._mat import scalar
from monalisa.rawDataReader.siemens._twix import read_twix


def bmSiemensReadRawData(obj, flagSS, flagExcludeSI):
    """Readouts ``[nCh, N, nSeg*nShot]`` of a Siemens file (see ``mleSiemensReader.readRawData``)."""
    p = obj.acquisitionParams
    nCh, N, nSeg, nShot = (int(scalar(v)) for v in (p.nCh, p.N, p.nSeg, p.nShot))
    nEcho, nShot_off = int(scalar(p.nEcho)), int(scalar(p.nShot_off))
    readouts = read_twix(obj.argFile).image.unsorted()
    if nEcho == 1:
        readouts = np.transpose(readouts, (1, 0, 2))
        readouts = np.reshape(readouts, (nCh, N, nSeg, nShot), order="F")
        if flagSS and nShot_off > 0:
            readouts = readouts[:, :, :, nShot_off:]
            nShot -= nShot_off
        if flagExcludeSI:
            readouts = readouts[:, :, 1:, :]
            nSeg -= 1
        return np.reshape(readouts, (nCh, N, nSeg * nShot), order="F")
    if nEcho == 2:
        raise NotImplementedError("bmTwix_data : nEcho == 2, case not implemented, yet.")
    raise NotImplementedError("bmTwix_data : case not implemented. ")
