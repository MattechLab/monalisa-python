"""Polygonal region of interest, the counterpart of MATLAB ``roipoly`` (Image Processing Toolbox)
used by the tutorial scripts (normalization ROI of mitosius_script.m)."""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from matplotlib.path import Path

from monalisa._mat import disp
from monalisa.display._qt import mpl_canvas, qt_app, run_dialog


def poly2mask(c, r, shape) -> np.ndarray:
    """Pixels of an image of size ``shape`` whose centre lies inside the polygon with vertices
    ``(c, r)`` (1-based column and row coordinates, as MATLAB ``poly2mask``; edge pixels can
    differ from MATLAB's sub-pixel rule)."""
    c = np.ravel(np.asarray(c, dtype=np.float64))
    r = np.ravel(np.asarray(r, dtype=np.float64))
    if c.size != r.size or c.size < 3:
        raise ValueError("roipoly: c and r must have the same length (at least 3 vertices)")
    rows, cols = np.meshgrid(np.arange(1, shape[0] + 1), np.arange(1, shape[1] + 1), indexing="ij")
    pts = np.column_stack([cols.ravel(), rows.ravel()])
    inside = Path(np.column_stack([c, r])).contains_points(pts, radius=1e-9)
    return inside.reshape(shape)


def roipoly(image, c=None, r=None):
    """Binary mask of a polygon drawn on ``image`` (2D, shown with rows down and columns across,
    as MATLAB ``imagesc``).

    ``roipoly(image)`` opens a window: click the vertices, close the polygon on the first vertex
    (it can then be moved and edited), and press Confirm. The vertices are printed, so the same
    mask can be rebuilt without the window: ``roipoly(image, c, r)`` with the 1-based column and
    row coordinates of the vertices (MATLAB ``roipoly(I, c, r)``).
    """
    im = np.asarray(image)
    if np.iscomplexobj(im):
        im = np.abs(im)
    if im.ndim != 2:
        raise ValueError("roipoly: image must be 2D")
    if c is not None or r is not None:
        return poly2mask(c, r, im.shape)
    dlg = dialog_class()(im)
    if not run_dialog(dlg) or dlg.vertices is None:
        raise RuntimeError("roipoly: no polygon confirmed")
    c, r = dlg.vertices
    disp(f"roipoly: c = [{', '.join(f'{v:.1f}' for v in c)}], r = [{', '.join(f'{v:.1f}' for v in r)}]")
    return poly2mask(c, r, im.shape)


@lru_cache(maxsize=1)
def dialog_class():
    """The Qt dialog class (Qt is imported on first use only)."""
    from matplotlib.widgets import PolygonSelector
    from qtpy.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

    class _RoiPolyDialog(QDialog):
        """Image with a matplotlib PolygonSelector; ``vertices`` = (c, r), 1-based, after Confirm."""

        def __init__(self, im):
            qt_app("Pass the polygon instead: roipoly(image, c, r).")
            super().__init__()
            self.setWindowTitle("roipoly")
            self.vertices = None
            self.fig, self.canvas = mpl_canvas(6, 6)
            ax = self.fig.add_subplot()
            # extent puts pixel (row i, column j) at 1-based coordinates (j, i), as MATLAB
            ax.imshow(im, cmap="gray", extent=(0.5, im.shape[1] + 0.5, im.shape[0] + 0.5, 0.5))
            ax.set_title("click the vertices, close on the first one, then Confirm", fontsize=9)
            self.selector = PolygonSelector(ax, lambda v: None, useblit=False,
                                            props={"color": "y", "linewidth": 1.5})
            ok = QPushButton("Confirm")
            ok.clicked.connect(self.confirm)
            cancel = QPushButton("Cancel")
            cancel.clicked.connect(self.reject)
            buttons = QHBoxLayout()
            buttons.addWidget(QLabel("Esc in the image restarts the polygon"))
            buttons.addStretch()
            buttons.addWidget(ok)
            buttons.addWidget(cancel)
            lay = QVBoxLayout(self)
            lay.addWidget(self.canvas)
            lay.addLayout(buttons)

        def set_vertices(self, c, r):
            self.selector.verts = list(zip(np.ravel(c), np.ravel(r), strict=True))

        def confirm(self):
            v = np.asarray(self.selector.verts, dtype=np.float64)
            if v.shape[0] < 3:
                return
            self.vertices = (v[:, 0], v[:, 1])
            self.accept()

    return _RoiPolyDialog
