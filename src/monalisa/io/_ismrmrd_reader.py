"""Port of src/rawDataReader/ismrmrd/mleIsmrmrdReader.m."""

from monalisa.io._raw_data_reader import RawDataReader


class IsmrmrdReader(RawDataReader):
    """Reader of ISMRMRD ``.mrd`` files."""

    def read_meta_data(self):
        from monalisa.io._ismrmrd_read_meta_data import ismrmrd_read_meta_data

        return ismrmrd_read_meta_data(self)

    def read_raw_data(self, flagSS=False, flagExcludeSI=False):
        from monalisa.io._ismrmrd_read_raw_data import ismrmrd_read_raw_data

        return ismrmrd_read_raw_data(self, flagSS, flagExcludeSI)
