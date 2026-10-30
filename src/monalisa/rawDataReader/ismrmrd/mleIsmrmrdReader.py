"""Port of src/rawDataReader/ismrmrd/mleIsmrmrdReader.m."""

from monalisa.rawDataReader.mleRawDataReader import mleRawDataReader


class mleIsmrmrdReader(mleRawDataReader):
    """Reader of ISMRMRD ``.mrd`` files."""

    def readMetaData(self):
        from monalisa.rawDataReader.ismrmrd.dhIsmrmrdReadMetaData import dhIsmrmrdReadMetaData

        return dhIsmrmrdReadMetaData(self)

    def readRawData(self, flagSS=False, flagExcludeSI=False):
        from monalisa.rawDataReader.ismrmrd.dhIsmrmrdReadRawData import dhIsmrmrdReadRawData

        return dhIsmrmrdReadRawData(self, flagSS, flagExcludeSI)
