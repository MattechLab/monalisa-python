"""Port of src/rawDataReader/siemens/mleSiemensReader.m."""

from monalisa.io._raw_data_reader import RawDataReader


class SiemensReader(RawDataReader):
    """Reader of Siemens twix ``.dat`` files."""

    def read_meta_data(self):
        from monalisa.io._siemens_read_meta_data import siemens_read_meta_data

        return siemens_read_meta_data(self)

    def read_raw_data(self, flagSS=False, flagExcludeSI=False):
        """Readouts ``[nCh, N, nLine]``; ``flagSS`` drops the non steady-state shots,
        ``flagExcludeSI`` the self-navigation (first) segment of each shot."""
        from monalisa.io._siemens_read_raw_data import siemens_read_raw_data

        return siemens_read_raw_data(self, flagSS, flagExcludeSI)
