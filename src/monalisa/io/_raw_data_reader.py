"""Port of src/rawDataReader/mleRawDataReader.m (abstract reader)."""

from __future__ import annotations


class RawDataReader:
    """Raw data reader: ``argFile``, ``autoFlag`` (no user interaction when true)
    and the ``acquisitionParams`` read at construction."""

    def __init__(self, filepath, autoFlag):
        self.argFile = filepath
        self.autoFlag = autoFlag
        self.acquisitionParams = self.read_meta_data()

    def read_meta_data(self):
        raise NotImplementedError("read_meta_data must be implemented by the subclass")

    def read_raw_data(self, flagSS=False, flagNoSI=False):
        raise NotImplementedError("read_raw_data must be implemented by the subclass")

    @classmethod
    def from_matlab_fields(cls, fields: dict):
        """Rebuild a reader recorded in MATLAB without reading the file again."""
        obj = cls.__new__(cls)
        obj.argFile = fields.get("argFile")
        auto = fields.get("autoFlag")
        obj.autoFlag = None if auto is None else bool(auto)
        obj.acquisitionParams = fields.get("acquisitionParams")
        return obj
