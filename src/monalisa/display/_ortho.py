"""ITK-SNAP-like layout for show_image: three linked slice views and a 3D view in one window.

Each view is a napari canvas (``napari.qt.QtViewer``) showing the same image: "along z" (top
left), "along x" (top right), 3D (bottom left) and "along y" (bottom right). They share one
cursor position: clicking in a slice view moves the other two slices there (and draws the
crosshair), the slice sliders below each view move it too, and the time slider and the contrast
apply to all views.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from monalisa.display._show_image import AXIS_LABELS

# view -> (sliced axis, row axis, column axis); rows and columns as in the notebook viewer
SLICE_VIEWS = {"along z": (2, 0, 1), "along x": (0, 1, 2), "along y": (1, 2, 0)}
VIEW_3D = (2, 0, 1)  # displayed axes of the 3D view: volume of x, y, z
GRID = {"along z": (0, 0), "along x": (0, 1), "3D": (1, 0), "along y": (1, 1)}
RENDERINGS = ("mip", "attenuated_mip", "average", "translucent", "iso", "minip")
CROSSHAIR_COLOR = "#3fa9ff"

_OPEN: set = set()  # windows stay alive while open, even if the caller keeps no reference


def dims_order(nd: int, k: int, r: int, c: int) -> tuple:
    """napari ``dims.order`` slicing axis ``k`` and displaying rows ``r``, columns ``c``; the
    remaining axes (t, ...) come first, so they get sliders."""
    rest = tuple(d for d in range(nd - 1, -1, -1) if d not in (k, r, c))
    return rest + (k, r, c)


class OrthoViewer:
    """The window of ``show_image(x, view="ortho")``.

    ``point`` is the cursor position (0-based indices of x, y, z, t, ...); ``set_point`` moves it.
    ``models`` holds the napari ``ViewerModel`` of each view and ``images`` its image layer.
    """

    def __init__(self, x: np.ndarray, name: str | None = None, contrast_limits=None):
        from napari.components import ViewerModel
        from napari.qt import QtViewer, get_qapp

        get_qapp()  # napari's Qt application (in IPython / Jupyter it also starts the Qt event loop)
        if x.ndim < 3:
            raise ValueError("show_image: layout='orthogonal' needs a 3D (or 4D, 5D) image")
        self.x, self.name = x, name
        nd = x.ndim
        lims = tuple(contrast_limits) if contrast_limits is not None else (float(np.min(x)), float(np.max(x)))
        if lims[1] <= lims[0]:
            lims = (lims[0], lims[0] + 1.0)
        self.models, self.images, self.crosshairs, self.qt_viewers = {}, {}, {}, {}
        self._syncing = False
        self._on_close = []
        for view in GRID:
            m = ViewerModel(title=view)
            qv = self.qt_viewers[view] = QtViewer(m)
            _ = qv.controls  # created on first access; it must exist before the layers are added
            img = m.add_image(x, name=name or "image", colormap="gray", contrast_limits=lims)
            m.dims.axis_labels = AXIS_LABELS[:nd]
            if view == "3D":
                m.dims.order = dims_order(nd, *VIEW_3D)
                m.dims.ndisplay = 3
            else:
                m.dims.order = dims_order(nd, *SLICE_VIEWS[view])
                self.crosshairs[view] = m.add_shapes(ndim=nd, name="crosshair", edge_color=CROSSHAIR_COLOR,
                                                     face_color="transparent", opacity=0.8)
                m.mouse_drag_callbacks.append(self._click_callback(view))
            m.layers.selection.active = img
            m.reset_view()
            self.models[view], self.images[view] = m, img
        for view, m in self.models.items():
            m.dims.events.current_step.connect(lambda _e, v=view: self._step_changed(v))
        for attr in ("contrast_limits", "gamma", "colormap"):
            for view, img in self.images.items():
                getattr(img.events, attr).connect(lambda _e, v=view, a=attr: self._sync_display(v, a))
        self.window = window_class()(self)
        self.set_point([n // 2 for n in x.shape[:3]] + [0] * (nd - 3))

    # --- cursor ----------------------------------------------------------------------------

    @property
    def point(self) -> tuple:
        return tuple(int(i) for i in self.models["along z"].dims.current_step)

    def set_point(self, point):
        """Move the cursor to ``point`` (0-based indices; values outside the image are clipped)."""
        p = [int(np.clip(round(float(v)), 0, n - 1)) for v, n in zip(point, self.x.shape, strict=True)]
        self.models["along z"].dims.current_step = tuple(p)  # propagated by _step_changed

    def _step_changed(self, view):
        if self._syncing:
            return
        self._syncing = True
        try:
            step = self.models[view].dims.current_step
            for other, m in self.models.items():
                if other != view and m.dims.current_step != step:
                    m.dims.current_step = step
        finally:
            self._syncing = False
        self._update_crosshairs()
        self.window.update_readout()

    def _click_callback(self, view):
        k, r, c = SLICE_VIEWS[view]

        def on_press(model, event):
            # a click (press and release without moving) sets the cursor; a drag pans as usual
            if event.button != 1:
                return
            moved = False
            yield
            while event.type == "mouse_move":
                moved = True
                yield
            if not moved:
                p = list(self.point)
                p[r], p[c] = event.position[r], event.position[c]
                self.set_point(p)

        return on_press

    def _update_crosshairs(self):
        p = np.asarray(self.point, dtype=float)
        width = max(self.x.shape[:3]) / 250
        for view, layer in self.crosshairs.items():
            k, r, c = SLICE_VIEWS[view]
            lines = []
            for along in (c, r):  # line at row p[r] across the columns, and at column p[c] down the rows
                # endpoints on pixel centres: lines reaching beyond them would widen napari's
                # world range, which shifts the slider indices of all views
                a, b = p.copy(), p.copy()
                a[along], b[along] = 0, self.x.shape[along] - 1
                lines.append(np.stack([a, b]))
            layer.selected_data = set()
            layer.data = []
            layer.add_lines(lines, edge_width=width, edge_color=CROSSHAIR_COLOR)

    def _sync_display(self, view, attr):
        if self._syncing:
            return
        self._syncing = True
        try:
            value = getattr(self.images[view], attr)
            for other, img in self.images.items():
                if other != view:
                    setattr(img, attr, value)
        finally:
            self._syncing = False

    # --- window ------------------------------------------------------------------------------

    def show(self, block: bool = False):
        self.window.show()
        _OPEN.add(self)
        if block:
            from qtpy.QtCore import QEventLoop

            loop = QEventLoop()
            self._on_close.append(loop.quit)
            loop.exec()
        return self

    def close(self):
        self.window.close()

    def _closed(self):
        for qv in self.qt_viewers.values():
            qv.close()
        _OPEN.discard(self)
        for f in self._on_close:
            f()

    def __repr__(self):
        shape = "x".join(str(n) for n in self.x.shape)
        return f"<show_image orthogonal viewer{': ' + self.name if self.name else ''} ({shape})>"


@lru_cache(maxsize=1)
def window_class():
    from napari.qt import get_stylesheet
    from qtpy.QtCore import Qt
    from qtpy.QtWidgets import QComboBox, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

    class OrthoWindow(QWidget):
        def __init__(self, ov: OrthoViewer):
            super().__init__()
            self.ov = ov
            self.setWindowTitle(ov.name or "monalisa")
            self.setStyleSheet(get_stylesheet("dark"))
            lay = QHBoxLayout(self)

            side = QVBoxLayout()
            self.readout = QLabel()
            self.readout.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            side.addWidget(QLabel("<b>Cursor</b> (click in a slice view)"))
            side.addWidget(self.readout)
            side.addWidget(QLabel("<b>Display</b> (all views)"))
            side.addWidget(ov.qt_viewers["along z"].controls)
            side.addWidget(QLabel("<b>3D rendering</b>"))
            self.rendering = QComboBox()
            self.rendering.addItems(RENDERINGS)
            self.rendering.setCurrentText(ov.images["3D"].rendering)
            self.rendering.currentTextChanged.connect(lambda t: setattr(ov.images["3D"], "rendering", t))
            side.addWidget(self.rendering)
            side.addStretch()
            panel = QWidget()
            panel.setLayout(side)
            panel.setFixedWidth(300)
            lay.addWidget(panel)

            grid = QGridLayout()
            for view, (i, j) in GRID.items():
                cell = QVBoxLayout()
                if view == "3D":
                    title = "3D (rotate: drag, zoom: wheel)"
                else:
                    k, r, c = SLICE_VIEWS[view]
                    title = f"{view}  (rows {AXIS_LABELS[r]}, columns {AXIS_LABELS[c]})"
                cell.addWidget(QLabel(title))
                cell.addWidget(ov.qt_viewers[view], 1)
                w = QWidget()
                w.setLayout(cell)
                grid.addWidget(w, i, j)
            lay.addLayout(grid, 1)
            self.resize(1300, 950)

        def update_readout(self):
            ov = self.ov
            p = ov.point
            parts = [f"{AXIS_LABELS[d]} = {p[d] + 1} / {ov.x.shape[d]}" for d in range(ov.x.ndim)]
            self.readout.setText("<br>".join(parts) + f"<br>value = {float(ov.x[p]):.4g}")

        def closeEvent(self, event):
            self.ov._closed()
            super().closeEvent(event)

    return OrthoWindow
