"""Port of src/rawDataReader/createRawDataReader.m."""

import os

from monalisa.io._ismrmrd_reader import IsmrmrdReader
from monalisa.io._siemens_reader import SiemensReader


def create_raw_data_reader(filepath, autoFlag):
    """Reader for a raw data file, chosen by extension (``.dat`` Siemens, ``.mrd`` ISMRMRD)."""
    ext = os.path.splitext(os.fspath(filepath))[1].lower()
    if ext == ".mrd":
        return IsmrmrdReader(filepath, autoFlag)
    if ext == ".dat":
        return SiemensReader(filepath, autoFlag)
    raise ValueError(f"Unsupported file extension: {ext}")
