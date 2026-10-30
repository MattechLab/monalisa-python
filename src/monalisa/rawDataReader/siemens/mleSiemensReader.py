"""Port of src/rawDataReader/siemens/mleSiemensReader.m."""

from monalisa.rawDataReader.mleRawDataReader import mleRawDataReader


class mleSiemensReader(mleRawDataReader):
    """Reader of Siemens twix ``.dat`` files."""

    def readMetaData(self):
        from monalisa.rawDataReader.siemens.dhSiemensReadMetaData import dhSiemensReadMetaData

        return dhSiemensReadMetaData(self)

    def readRawData(self, flagSS=False, flagExcludeSI=False):
        """Readouts ``[nCh, N, nLine]``; ``flagSS`` drops the non steady-state shots,
        ``flagExcludeSI`` the self-navigation (first) segment of each shot."""
        from monalisa.rawDataReader.siemens.bmSiemensReadRawData import bmSiemensReadRawData

        return bmSiemensReadRawData(self, flagSS, flagExcludeSI)
