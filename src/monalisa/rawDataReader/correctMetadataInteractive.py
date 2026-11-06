"""Port of src/rawDataReader/correctMetadataInteractive.m (Qt dialog instead of uifigure)."""

from monalisa.rawDataReader import _metadata_dialog


def correctMetadataInteractive(myMriAcquisition_node, reconFoV):
    """Let the user correct the extracted acquisition parameters in a table (N, nLine, nShot, nSeg,
    nCh, nEcho, nShotOff, FoV, reconstruction FoV), the navigation type and the oversampling
    flag. Waits until Confirm; Cancel or closing keeps the extracted values.

    Opened by the raw data readers when ``autoFlag`` is false or the FoV could not be read.
    Without a window: ``autoFlag=True`` and set ``reader.acquisitionParams`` fields in the code.
    Returns ``(myMriAcquisition_node, reconFoV)``.
    """
    return _metadata_dialog.run(myMriAcquisition_node, reconFoV)
