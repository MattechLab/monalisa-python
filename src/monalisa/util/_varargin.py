"""Port of src/varargin/bmVarargin.m."""

from monalisa._mat import cell_items, isempty


def varargin(myCell=None, nargout=1):
    """Unpack the cell ``myCell`` into ``nargout`` values, padding with ``None``.

    In the Python port optional arguments are keyword arguments; this
    function is kept for code that forwards MATLAB-style ``varargin`` cells.
    """
    items = [] if isempty(myCell) else cell_items(myCell)
    out = items + [None] * max(nargout - len(items), 0)
    if nargout == 1:
        return out[0]
    return tuple(out[:nargout])
