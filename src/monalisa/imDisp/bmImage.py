"""Python counterpart of src/imDisp/bmImage.m (2D to 5D image viewer).

Not a line-by-line port: MATLAB's bmImage2..5 figures with their keyboard shortcuts are replaced
by napari (https://napari.org), which offers the same functions (slice and frame sliders, views
along x, y or z, contrast, points) plus 3D rendering. In a Jupyter notebook, a light viewer with
sliders is used instead (no window needed).
"""

from __future__ import annotations

import numpy as np

from monalisa._mat import iscell, squeeze
from monalisa.arrayUtility.bmCell2Array import bmCell2Array
from monalisa.imDisp._qt import check_display, in_jupyter

AXIS_LABELS = ("x", "y", "z", "t", "u")


def image_data(argImage) -> np.ndarray:
    """The array displayed by bmImage: cells are stacked (one frame per cell, ``bmCell2Array``
    then ``squeeze``), complex values become magnitudes and logical values numbers."""
    if iscell(argImage):
        argImage = squeeze(bmCell2Array(argImage))
    x = np.asarray(argImage)
    if np.iscomplexobj(x):
        x = np.abs(x)
    if x.dtype == bool:
        x = x.astype(np.float64)
    if x.ndim == 1:
        x = x[:, None]
    while x.ndim > 2 and x.shape[-1] == 1:  # MATLAB drops trailing singleton dimensions
        x = x[..., 0]
    if x.ndim > 5:
        raise ValueError(f"bmImage: {x.ndim}-D arrays are not supported (2 to 5)")
    return x


def view_order(ndim: int) -> tuple:
    """napari dimension order showing ``x(:, :, k, ...)`` as MATLAB does: rows x, columns y,
    sliders for z, t, ... (the data keep the MATLAB axis order, so napari coordinates are
    MATLAB indices minus one)."""
    return tuple(range(ndim - 1, 1, -1)) + (0, 1)


VIEWS = ("inline", "window", "3d", "ortho")


def bmImage(argImage, view: str | None = None, *, name: str | None = None, contrast=None,
            block: bool = False, viewer=None, **old_names):
    """Show a 2D, 3D, 4D or 5D image (or a cell / list of equally sized frames).

    Axes keep the MATLAB layout ``(x, y, z, t, ...)``: the slice ``x(:, :, k)`` is shown with x
    down the rows and y along the columns, as in MATLAB, and z, t have sliders. Complex images
    are shown as magnitudes.

    Parameters
    ----------
    argImage : the image, or a list / cell of frames of the same size (stacked along t).
    view : how to show it:

        - ``"inline"``: sliders and the slice below the cell (Jupyter only, no window);
        - ``"window"``: a napari window with one slice view (views along x, y or z, contrast,
          points; the cube button at its bottom left switches to 3D);
        - ``"3d"``: the same window, opened in 3D (volume rendering, rotate with the mouse);
        - ``"ortho"``: one window laid out like ITK-SNAP: the slices along z, x and y and a 3D
          view, linked by a cursor (click in a slice view to move it).

        Default: ``"inline"`` in Jupyter, ``"window"`` otherwise. Windows also open from Jupyter,
        next to the notebook (they need a display).
    name : title of the window and name of the image.
    contrast : ``(low, high)`` display range; default: the data range.
    block : in a script, wait until the window is closed. Windows opened from a script close when
        it ends: pass ``block=True`` on the last call (like ``plt.show()``). Not needed in
        Jupyter.
    viewer : add the image as a new layer of this napari ``Viewer`` (returned by an earlier
        ``bmImage`` call) instead of opening a new window, e.g. to compare two reconstructions.

    Returns
    -------
    The viewer, to keep working with it from code: a napari ``Viewer`` (``"window"``, ``"3d"``;
    its layers hold the data and any points placed), an ``OrthoViewer`` (``"ortho"``: ``.point``,
    ``.set_point``) or the notebook viewer (``"inline"``).
    """
    view, contrast = _old_names(view, contrast, old_names)
    x = image_data(argImage)
    if view is None:
        view = "inline" if in_jupyter() and viewer is None else "window"
    if view not in VIEWS:
        raise ValueError(f"bmImage: unknown view {view!r} (one of {', '.join(VIEWS)})")
    if viewer is not None and view not in ("window", "3d"):
        raise ValueError(f"bmImage: viewer= adds to a napari window (view 'window' or '3d', not {view!r})")
    if view in ("3d", "ortho") and x.ndim < 3:
        raise ValueError(f"bmImage: view {view!r} needs a 3D (or 4D, 5D) image, got {x.ndim}D")
    if view == "inline":
        from monalisa.imDisp._notebook import NotebookViewer

        w = NotebookViewer(x, name=name, contrast_limits=contrast)
        w.show()
        return w

    check_display("In Jupyter, use view='inline', or save the image and view it elsewhere.")
    if view == "ortho":
        from monalisa.imDisp._ortho import OrthoViewer

        return OrthoViewer(x, name=name, contrast_limits=contrast).show(block=block)
    import napari  # creates the Qt application and, in IPython / Jupyter, starts its Qt event loop

    if viewer is None:
        viewer = napari.Viewer(title=name or "bmImage")
    kw = {} if contrast is None else {"contrast_limits": tuple(contrast)}
    viewer.add_image(x, name=name or "image", colormap="gray", **kw)
    if viewer.dims.ndim == x.ndim:
        viewer.dims.axis_labels = AXIS_LABELS[: x.ndim]
        viewer.dims.order = view_order(x.ndim)
    if view == "3d":
        viewer.dims.ndisplay = 3
    if block:
        napari.run()
    return viewer


def _old_names(view, contrast, old: dict):
    """Earlier keywords (backend, render3d, layout, contrast_limits) still work, with a warning."""
    if not old:
        return view, contrast
    import warnings

    unknown = set(old) - {"backend", "render3d", "layout", "contrast_limits"}
    if unknown:
        raise TypeError(f"bmImage() got unexpected keyword arguments: {', '.join(sorted(unknown))}")
    if old.get("layout") == "orthogonal":
        new = "ortho"
    elif old.get("render3d"):
        new = "3d"
    else:
        new = {"notebook": "inline", "napari": "window"}.get(old.get("backend"))
    if "contrast_limits" in old:
        contrast = old["contrast_limits"]
    hint = (f"view={new!r}" if new else "") + (", " if new and "contrast_limits" in old else "") + (
        "contrast=(low, high)" if "contrast_limits" in old else "")
    warnings.warn(f"bmImage: {', '.join(sorted(old))} are replaced by: {hint}", FutureWarning, stacklevel=3)
    return view or new, contrast
