"""Port of src/rawDataReader/createRawDataReader.m."""

import os

from monalisa.rawDataReader.siemens.mleSiemensReader import mleSiemensReader


def createRawDataReader(filepath, autoFlag):
    """Reader for a raw data file, chosen by extension (``.dat`` Siemens, ``.mrd`` ISMRMRD)."""
    ext = os.path.splitext(os.fspath(filepath))[1].lower()
    if ext == ".mrd":
        raise NotImplementedError("The ISMRMRD reader is not ported yet")
    if ext == ".dat":
        return mleSiemensReader(filepath, autoFlag)
    raise ValueError(f"Unsupported file extension: {ext}")
