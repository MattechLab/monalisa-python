"""Port of src/rawDataReader/checkMetadataInteractive.m (one Qt dialog instead of a figure and a
uifigure)."""

from monalisa.rawDataReader import _metadata_dialog


def checkMetadataInteractive(mySI, s_mean, s_center_mass, myMriAcquisition_node, reconFoV):
    """Plot the self-navigation magnitude of the first segment of every shot (with its mean and
    centre of mass), with a draggable line at the estimated steady-state shot ``nShot_off``, above
    the editable parameter table of :func:`correctMetadataInteractive`. Waits until Confirm.

    Without a window: ``autoFlag=True`` and set ``reader.acquisitionParams.nShot_off`` etc.
    Returns ``(myMriAcquisition_node, reconFoV)``.
    """
    return _metadata_dialog.run(myMriAcquisition_node, reconFoV, (mySI, s_mean, s_center_mass))
