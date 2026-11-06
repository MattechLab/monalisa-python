"""Qt dialog of thresholdRMS_MIP (interactive mode)."""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from monalisa.imDisp._qt import mpl_canvas, qt_app

# MATLAB permutations of the views: "Along X" [2,3,1], "Along Y" [3,1,2], "Along Z" [1,2,3]
VIEWS = {"Along X": (1, 2, 0), "Along Y": (2, 0, 1), "Along Z": (0, 1, 2)}
HINT = "Pass th_RMS and th_MIP to bmCoilSense_nonCart_mask_automatic, or use autoFlag=True."


def fraction_above(data, colorMax) -> np.ndarray:
    """Fraction of voxels with a value above each integer 0 .. colorMax-1."""
    d = np.ravel(data)
    return np.array([np.count_nonzero(d > i) / d.size for i in range(colorMax)])


def thresholded_slice(data, view, curImNum, th, useContrast) -> np.ndarray:
    """``permute(data, perm)(:, :, curImNum)`` with the threshold applied, as MATLAB refreshImage."""
    im = np.transpose(data, VIEWS[view])[:, :, curImNum - 1].copy()
    if useContrast:
        return im > th
    im[im <= th] = 0
    return im


@lru_cache(maxsize=1)
def dialog_class():
    from qtpy.QtWidgets import QCheckBox, QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

    class ThresholdDialog(QDialog):
        def __init__(self, colorMax, dataRMS, dataMIP, thRMS, thMIP):
            qt_app(HINT)
            super().__init__()
            self.setWindowTitle("thresholdRMS_MIP")
            self.colorMax = int(colorMax)
            self.data = {"RMS": dataRMS, "MIP": dataMIP}
            self.th = {"RMS": float(thRMS), "MIP": float(thMIP)}
            self.view = "Along Z"
            self.curImNum = min(24, dataRMS.shape[2])
            self.useContrast = False
            self._active = None

            self.fig, self.canvas = mpl_canvas(8, 7)
            gs = self.fig.add_gridspec(2, 2)
            self.axSel = self.fig.add_subplot(gs[0, :])
            self.ax = {"RMS": self.fig.add_subplot(gs[1, 0]), "MIP": self.fig.add_subplot(gs[1, 1])}
            x = np.arange(self.colorMax)
            self.axSel.plot(x, fraction_above(dataRMS, self.colorMax), ".-", label="RMS")
            self.axSel.plot(x, fraction_above(dataMIP, self.colorMax), ".-", label="MIP")
            self.line = {"RMS": self.axSel.axvline(self.th["RMS"], color="b", linewidth=2, label="RMS TH"),
                         "MIP": self.axSel.axvline(self.th["MIP"], color="r", linewidth=2, label="MIP TH")}
            self.axSel.set_xlabel("X")
            self.axSel.set_ylabel("Fraction above X")
            self.axSel.legend()
            self.axSel.set_title("Fraction of points having a value above X (drag the thresholds; "
                                 "scroll to change slice)", fontsize=9)
            self.images = {}
            for k, ax in self.ax.items():
                self.images[k] = ax.imshow(self.slice(k), cmap="gray")
                ax.set_axis_off()
            self.refresh()
            self.canvas.mpl_connect("button_press_event", self._press)
            self.canvas.mpl_connect("motion_notify_event", self._motion)
            self.canvas.mpl_connect("button_release_event", self._release)
            self.canvas.mpl_connect("scroll_event", self._scroll)

            views = QComboBox()
            views.addItems(list(VIEWS))
            views.setCurrentText(self.view)
            views.currentTextChanged.connect(self.set_view)
            contrast = QCheckBox("Contrast")
            contrast.toggled.connect(self.set_contrast)
            ok = QPushButton("Confirm Selection")
            ok.clicked.connect(self.accept)
            self.label = QLabel()
            bar = QHBoxLayout()
            for w in (contrast, views, self.label):
                bar.addWidget(w)
            bar.addStretch()
            bar.addWidget(ok)
            lay = QVBoxLayout(self)
            lay.addWidget(self.canvas)
            lay.addLayout(bar)
            self._update_label()
            self.resize(850, 800)

        def slice(self, k):
            return thresholded_slice(self.data[k], self.view, self.curImNum, self.th[k], self.useContrast)

        def nslices(self):
            return self.data["RMS"].shape[VIEWS[self.view][2]]

        def refresh(self):
            for k, ax in self.ax.items():
                im = self.slice(k).astype(np.float64)
                self.images[k].set_data(im)
                self.images[k].set_extent((-0.5, im.shape[1] - 0.5, im.shape[0] - 0.5, -0.5))
                self.images[k].set_clim(float(im.min()), float(im.max()) if im.max() > im.min() else 1.0)
                ax.set_title(f"{k} [{self.curImNum}/{self.nslices()}]", fontsize=9)
            self.canvas.draw_idle()

        def _update_label(self):
            self.label.setText(f"th_RMS = {self.th['RMS']:g}   th_MIP = {self.th['MIP']:g}")

        def set_threshold(self, k, value):
            value = max(min(round(value), self.colorMax - 1), 0)
            self.th[k] = float(value)
            self.line[k].set_xdata([value, value])
            self._update_label()
            self.refresh()

        def set_view(self, view):
            self.view = view
            self.curImNum = min(self.curImNum, self.nslices())
            self.refresh()

        def set_contrast(self, on):
            self.useContrast = bool(on)
            self.refresh()

        def set_slice(self, n):
            self.curImNum = (n - 1) % self.nslices() + 1  # wraps around, as MATLAB
            self.refresh()

        def _press(self, ev):
            if ev.inaxes is not self.axSel or ev.xdata is None:
                return
            for k in ("RMS", "MIP"):
                if abs(ev.xdata - self.th[k]) < 0.8:
                    self._active = k
                    return

        def _motion(self, ev):
            if self._active is not None and ev.xdata is not None:
                self.set_threshold(self._active, ev.xdata)

        def _release(self, ev):
            self._active = None

        def _scroll(self, ev):
            self.set_slice(self.curImNum + (1 if ev.button == "up" else -1))

    return ThresholdDialog
