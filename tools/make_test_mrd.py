"""Convert a Siemens twix file to ISMRMRD (.mrd) to test the ISMRMRD readers.

Usage:
    python tools/make_test_mrd.py bodyCoil.dat bodyCoil.mrd

Every image readout becomes one acquisition (in acquisition order) with its
time stamp, number of samples, active channels and the shot index in
``idx.segment``; the XML header carries the encoded/recon field of view
(half the Monalisa FoV, as Monalisa doubles it for the readout oversampling).
"""

import sys

import ismrmrd
import numpy as np

from monalisa.io._twix import read_twix


def convert(src, dst):
    tw = read_twix(src)
    img = tw.image
    fov = float(tw.hdr["Dicom"]["dReadoutFOV"])  # mm, without oversampling

    n = int(img.NCol)
    space = (f"<matrixSize><x>{n}</x><y>{n}</y><z>{n}</z></matrixSize>"
             f"<fieldOfView_mm><x>{fov}</x><y>{fov}</y><z>{fov}</z></fieldOfView_mm>")
    xml = ('<?xml version="1.0" encoding="utf-8"?>'
           '<ismrmrdHeader xmlns="http://www.ismrm.org/ISMRMRD">'
           "<experimentalConditions><H1resonanceFrequency_Hz>123000000</H1resonanceFrequency_Hz>"
           "</experimentalConditions><encoding>"
           f"<encodedSpace>{space}</encodedSpace><reconSpace>{space}</reconSpace>"
           "<encodingLimits/><trajectory>radial</trajectory></encoding></ismrmrdHeader>")

    ds = ismrmrd.Dataset(dst, "dataset", create_if_needed=True)
    ds.write_xml_header(xml)
    for mdb in img._mdbs:
        h = mdb.mdh
        data = np.asarray(mdb.data, dtype=np.complex64)  # (nCh, nCol)
        acq = ismrmrd.Acquisition.from_array(data)
        acq.acquisition_time_stamp = int(h.TimeStamp)
        acq.idx.kspace_encode_step_1 = int(h.Counter.Lin)
        acq.idx.segment = int(h.Counter.Seg)
        acq.idx.contrast = int(h.Counter.Eco)
        ds.append_acquisition(acq)
    ds.close()


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])
