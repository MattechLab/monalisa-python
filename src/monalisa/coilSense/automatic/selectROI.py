"""Port of src/coilSense/automatic/selectROI.m (one Qt window instead of two figures)."""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from monalisa._mat import disp, mround, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.imDisp._qt import mpl_canvas, qt_app, run_dialog

# projection -> (summed axis, row axis, column axis) of MATLAB's xRMS / yRMS / zRMS images
VIEWS = {"Along X": (0, 1, 2), "Along Y": (1, 2, 0), "Along Z": (2, 0, 1)}
AXES = "xyz"


def projection(data, view) -> np.ndarray:
    """Normalized sum along one axis, rows and columns as in MATLAB (permute, then sum(., 3))."""
    s, r, c = VIEWS[view]
    p = np.sum(np.transpose(data, (r, c, s)), axis=2)
    lo, hi = p.min(), p.max()
    return (p - lo) / (hi - lo) if hi > lo else p * 0


def border_extraction(edges, N_u) -> np.ndarray:
    """Rectangle edges (pixel-edge coordinates in [0.5, N + 0.5]) to the returned 1-based voxel
    indices ``[xMin, xMax; yMin, yMax; zMin, zMax]`` (MATLAB borderExtraction)."""
    out = np.zeros((3, 2))
    for k in range(3):
        N = N_u[k]
        for j in range(2):
            out[k, j] = mround(1 + ((edges[k][j] - 0.5) / N) * (N - 1))
    return out


def selectROI(dataRMS, dataMIP, N_u, autoFlag=None, boxPos=None):
    """Bounding box of the region of interest, drawn on the RMS and MIP images summed along x, y
    and z (6 images; moving one rectangle updates the others, and the limits can be typed in).
    ``boxPos`` = ``[xMin, xWidth; yMin, yWidth; zMin, zWidth]`` is the initial box (default
    ``[2, min(N_u) - 4]`` on every axis). Waits until Confirm.

    Returns ``[xMin, xMax; yMin, yMax; zMin, zMax]`` (1-based). Closing the window without
    confirming returns the initial box. Without a window: pass ``borders`` to
    bmCoilSense_nonCart_mask_automatic.
    """
    N_u = vec(N_u)
    dataRMS = bmBlockReshape(dataRMS, N_u)
    dataMIP = bmBlockReshape(dataMIP, N_u)
    if boxPos is None:
        boxPos = np.tile([2.0, np.min(N_u) - 4], (3, 1))
    boxPos = np.asarray(boxPos, dtype=np.float64)
    if autoFlag is None:
        autoFlag = False
    coordinates = np.column_stack([boxPos[:, 0], boxPos[:, 0] + boxPos[:, 1]])
    dlg = dialog_class()(dataRMS, dataMIP, N_u, boxPos, editable=not autoFlag)
    if run_dialog(dlg):
        coordinates = border_extraction(dlg.edges, N_u)
        b = coordinates.astype(int).tolist()
        disp(f"selectROI: borders = [[{b[0][0]}, {b[0][1]}], [{b[1][0]}, {b[1][1]}], [{b[2][0]}, {b[2][1]}]]")
    else:
        disp("Use confirm to use the new values. Don't close the figures!")
    return coordinates


@lru_cache(maxsize=1)
def dialog_class():
    from matplotlib.widgets import RectangleSelector
    from qtpy.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

    class SelectROIDialog(QDialog):
        """``edges[k] = [low, high]`` per axis x, y, z, in pixel-edge coordinates."""

        def __init__(self, dataRMS, dataMIP, N_u, boxPos, editable=True):
            qt_app("Pass borders to bmCoilSense_nonCart_mask_automatic, or use autoFlag=True.")
            super().__init__()
            self.setWindowTitle("selectROI")
            self.N_u = [float(n) for n in N_u]
            self.edges = [[boxPos[k, 0], boxPos[k, 0] + boxPos[k, 1]] for k in range(3)]
            self.fig, self.canvas = mpl_canvas(11, 7)
            self.selectors = []
            for i, (name, data) in enumerate((("RMS", dataRMS), ("MIP", dataMIP))):
                for j, view in enumerate(VIEWS):
                    ax = self.fig.add_subplot(2, 3, 3 * i + j + 1)
                    p = projection(data, view)
                    ax.imshow(p, cmap="gray", extent=(0.5, p.shape[1] + 0.5, p.shape[0] + 0.5, 0.5))
                    _, r, c = VIEWS[view]
                    ax.set_xlabel(AXES[c].upper())
                    ax.set_ylabel(AXES[r].upper())
                    ax.set_title(f"{name} summed {view.lower()}", fontsize=9)
                    sel = RectangleSelector(ax, self._moved(view), interactive=True, useblit=False,
                                            props={"edgecolor": "c", "facecolor": "none", "linewidth": 1.5},
                                            ignore_event_outside=True)
                    self.selectors.append((view, sel))
            self.fields = {}
            grid = QGridLayout()
            for k, axis in enumerate(AXES):
                grid.addWidget(QLabel(f"{axis.upper()} min / max"), 0, 2 * k, 1, 2)
                for j, side in enumerate(("Min", "Max")):
                    f = QLineEdit()
                    f.setToolTip(f"{axis.upper()}{side} of the mask")
                    f.setReadOnly(not editable)
                    f.editingFinished.connect(lambda k=k, j=j: self._typed(k, j))
                    self.fields[(k, j)] = f
                    grid.addWidget(f, 1, 2 * k + j)
            ok = QPushButton("Confirm Selection")
            ok.clicked.connect(self.accept)
            bar = QHBoxLayout()
            bar.addLayout(grid)
            bar.addStretch()
            bar.addWidget(ok)
            lay = QVBoxLayout(self)
            lay.addWidget(self.canvas)
            lay.addLayout(bar)
            self.update_all()
            self.resize(1100, 800)

        def _moved(self, view):
            def onselect(press, _release):
                sel = next((s for v, s in self.selectors if v == view and s.ax is press.inaxes), None)
                if sel is None:
                    return
                x0, x1, y0, y1 = sel.extents
                _, r, c = VIEWS[view]
                self.edges[c] = [x0, x1]
                self.edges[r] = [y0, y1]
                self.update_all()

            return onselect

        def _typed(self, k, j):
            try:
                v = float(self.fields[(k, j)].text())
            except ValueError:
                self.update_all()
                return
            self.set_edge(k, j, v)

        def set_edge(self, k, j, v):
            self.edges[k][j] = min(max(0.5, v), self.N_u[k] + 0.5)
            self.update_all()

        def update_all(self):
            for view, sel in self.selectors:
                _, r, c = VIEWS[view]
                sel.extents = (*self.edges[c], *self.edges[r])
            for (k, j), f in self.fields.items():
                f.setText(f"{self.edges[k][j]:g}")
            self.canvas.draw_idle()

    return SelectROIDialog
