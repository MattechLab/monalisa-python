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
from monalisa.imDisp._qt import NoDisplayError, has_display, in_jupyter

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


def bmImage(argImage, *, name: str | None = None, backend: str | None = None, block: bool = False,
            viewer=None, contrast_limits=None, render3d: bool = False):
    """Show a 2D, 3D, 4D or 5D image (or a cell / list of equally sized frames).

    Axes keep the MATLAB layout ``(x, y, z, t, ...)``: the slice ``x(:, :, k)`` is shown with x
    down the rows and y along the columns, as in MATLAB, and z, t have sliders. Complex images
    are shown as magnitudes.

    Parameters
    ----------
    name : window / layer title (MATLAB code calls ``title`` after ``bmImage``).
    backend : ``"napari"`` (window), ``"notebook"`` (sliders below a Jupyter cell) or ``None``:
        notebook inside Jupyter, napari otherwise.
    block : napari only: wait until the window is closed. Windows opened from a plain script
        close when the script ends; pass ``block=True`` on the last call, or call
        ``napari.run()`` at the end (like ``plt.show()``).
    viewer : napari only: add the image as a new layer of this viewer instead of a new window.
    contrast_limits : ``(low, high)``; default: data range.
    render3d : open napari in 3D (volume rendering of x, y, z; rotate with the mouse). Also from
        a notebook, where the napari window opens next to it. Switch between 2D and 3D with the
        cube button at the bottom left of the window, or ``viewer.dims.ndisplay = 2 / 3``.

    Returns the napari ``Viewer`` (its layers hold the data and any points you place), or the
    notebook widget.
    """
    x = image_data(argImage)
    if backend is None:
        backend = "notebook" if in_jupyter() and viewer is None and not render3d else "napari"
    if backend == "notebook":
        if render3d:
            raise ValueError("bmImage: render3d needs the napari backend")
        from monalisa.imDisp._notebook import NotebookViewer

        w = NotebookViewer(x, name=name, contrast_limits=contrast_limits)
        w.show()
        return w
    if backend != "napari":
        raise ValueError(f"bmImage: unknown backend {backend!r} (napari or notebook)")

    if not has_display():
        raise NoDisplayError("bmImage needs a display for the napari window (none found). "
                             "Use backend='notebook' in Jupyter, or save the image and view it elsewhere.")
    import napari  # creates the Qt application and, in IPython / Jupyter, starts its Qt event loop

    if viewer is None:
        viewer = napari.Viewer(title=name or "bmImage")
    kw = {} if contrast_limits is None else {"contrast_limits": tuple(contrast_limits)}
    viewer.add_image(x, name=name or "image", colormap="gray", **kw)
    if viewer.dims.ndim == x.ndim:
        viewer.dims.axis_labels = AXIS_LABELS[: x.ndim]
        viewer.dims.order = view_order(x.ndim)
    if render3d:
        viewer.dims.ndisplay = 3
    if block:
        napari.run()
    return viewer
