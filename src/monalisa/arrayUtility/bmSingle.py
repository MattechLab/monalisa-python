"""Port of src/arrayUtility/bmSingle.m."""

from monalisa._mat import cell_from_items, cell_items, cell_shape, iscell, single


def bmSingle(a):
    """MATLAB ``single``, applied to every element of a cell."""
    if iscell(a):
        return cell_from_items([single(x) for x in cell_items(a)], cell_shape(a))
    return single(a)
