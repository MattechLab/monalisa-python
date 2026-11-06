"""Qt dialog shared by correctMetadataInteractive and checkMetadataInteractive."""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from monalisa.imDisp._qt import mpl_canvas, qt_app

PARAM_NAMES = ("N", "nLine", "nShot", "nSeg", "nCh", "nEcho", "nShotOff", "FoV (acq)", "FoV (recon)")
CASES = ("Non-Cartesian", "Cartesian", "Case 3")
NAVIGATION = ("SI Navigation", "Pilot Tone Navigation", "Other")
HINT = ("Use autoFlag=True and set the fields of reader.acquisitionParams (N, nShot_off, FoV, ...) "
        "in your code instead.")


def mode(x) -> float:
    """MATLAB ``mode``: most frequent value, the smallest one in case of a tie."""
    vals, counts = np.unique(np.ravel(np.asarray(x, dtype=np.float64)), return_counts=True)
    return float(vals[np.argmax(counts)])


def extracted_values(node, reconFoV) -> list:
    return [float(node.N), float(node.nLine), float(node.nShot), float(node.nSeg), float(node.nCh),
            float(node.nEcho), float(node.nShot_off), mode(node.FoV), mode(reconFoV)]


def apply_values(node, reconFoV, values, case, selfNav_flag=None, roosk_flag=None):
    """Write the table values back as MATLAB does (FoV and reconFoV become constant vectors of the
    size of ``node.FoV``). Returns ``(node, reconFoV)``."""
    if selfNav_flag is not None:
        node.selfNav_flag = bool(selfNav_flag)
    if roosk_flag is not None:
        node.roosk_flag = bool(roosk_flag)
    if case != "Non-Cartesian":
        raise NotImplementedError("Case not implemented yet")
    v = [np.float64(a) for a in values]
    node.N, node.nLine, node.nShot, node.nSeg, node.nCh, node.nEcho, node.nShot_off = v[:7]
    shape = np.shape(node.FoV) if np.ndim(node.FoV) else (1, 1)
    node.FoV = np.ones(shape) * v[7]
    reconFoV = np.ones(shape) * v[8]
    return node, reconFoV


@lru_cache(maxsize=1)
def dialog_class():
    from qtpy.QtCore import Qt
    from qtpy.QtGui import QColor
    from qtpy.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
    )

    class MetadataDialog(QDialog):
        """Table of the extracted acquisition parameters with an editable "User Value" column.

        With ``si`` = ``(mySI, s_mean, s_center_mass)`` the self-navigation magnitude of the first
        segment of every shot is plotted above the table, with a draggable line for nShotOff.
        """

        def __init__(self, node, reconFoV, si=None):
            qt_app(HINT)
            super().__init__()
            self.setWindowTitle("Manual Parameter Adjustment")
            self.extracted = extracted_values(node, reconFoV)
            lay = QVBoxLayout(self)
            title = QLabel("Adjust Acquisition Parameters")
            f = title.font()
            f.setBold(True)
            f.setPointSize(f.pointSize() + 3)
            title.setFont(f)
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(title)
            self.shot_line = None
            if si is not None:
                lay.addWidget(self._si_plot(*si, node.nShot_off))

            row = QHBoxLayout()
            self.table = QTableWidget(len(PARAM_NAMES), 3)
            self.table.setHorizontalHeaderLabels(["Acquisition Parameters", "Extracted Value", "User Value"])
            orange = QColor.fromRgbF(0.9290, 0.6940, 0.1250)
            for i, (name, val) in enumerate(zip(PARAM_NAMES, self.extracted, strict=True)):
                for j, text in enumerate((name, f"{val:g}", f"{val:g}")):
                    item = QTableWidgetItem(text)
                    if j < 2:
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    else:
                        item.setBackground(orange)
                    self.table.setItem(i, j, item)
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.resizeColumnsToContents()
            self.table.itemChanged.connect(self._table_changed)
            row.addWidget(self.table, 1)

            side = QVBoxLayout()
            self.case = QComboBox()
            self.case.addItems(CASES)
            self.navigation = QComboBox()
            self.navigation.addItems(NAVIGATION)
            if not node.selfNav_flag:
                self.navigation.setCurrentText("Other")
            self.roosk = QCheckBox("Remove oversampling")
            self.roosk.setChecked(bool(node.roosk_flag))
            ok = QPushButton("Confirm")
            ok.clicked.connect(self.accept)
            cancel = QPushButton("Cancel")
            cancel.clicked.connect(self.reject)
            for w in (self.case, self.navigation, self.roosk, ok, cancel):
                side.addWidget(w)
            side.addStretch()
            row.addLayout(side)
            lay.addLayout(row)
            self.resize(720, 800 if si is not None else 420)

        def _si_plot(self, mySI, s_mean, s_center_mass, shotOff):
            fig, canvas = mpl_canvas(7, 3.5)
            ax = fig.add_subplot()
            mySI = np.asarray(mySI)
            nShot = mySI.shape[1]
            # imagesc(mySI, [0, 3*mean]) with YDir normal: pixel (n, s) at (s, n), 1-based
            im = ax.imshow(mySI, cmap="gray", vmin=0, vmax=3 * float(np.mean(mySI)), origin="lower", aspect="auto",
                           extent=(0.5, nShot + 0.5, 0.5, mySI.shape[0] + 0.5), interpolation="nearest")
            fig.colorbar(im, ax=ax)
            s = np.arange(1, nShot + 1)
            ax.plot(s, np.ravel(s_center_mass), "g.-", label="Center of Mass")
            ax.plot(s, np.ravel(s_mean), "r.-", label="Mean")
            self.shot_line = ax.axvline(float(shotOff), color="c", linestyle="--", label="Steady State")
            self.shot_text = ax.text(0.02, 0.85, "", transform=ax.transAxes, backgroundcolor="white")
            self._set_shot(float(shotOff))
            ax.legend(loc="best")
            ax.set_xlabel("nShot")
            ax.set_ylabel("N")
            ax.set_title("Magnitude spectrum for first segment of each shot\n"
                         "(estimates which shots should be excluded; drag the dashed line)", fontsize=9)
            self._ax, self._canvas, self._dragging, self._nShot = ax, canvas, False, nShot
            canvas.mpl_connect("button_press_event", self._press)
            canvas.mpl_connect("motion_notify_event", self._motion)
            canvas.mpl_connect("button_release_event", self._release)
            return canvas

        def _set_shot(self, shot):
            self.shot_line.set_xdata([shot, shot])
            self.shot_text.set_text(f"shot = {int(shot)}")
            self.shot_text.set_x(min(max((shot - 0.5) / (self.shot_line.axes.get_xlim()[1] - 0.5) + 0.02, 0), 0.85))

        def _press(self, ev):
            if ev.inaxes is self._ax and ev.xdata is not None and abs(ev.xdata - self.shot_line.get_xdata()[0]) < 10:
                self._dragging = True

        def _motion(self, ev):
            if self._dragging and ev.xdata is not None:
                lo, hi = self._ax.get_xlim()
                self._set_shot(max(min(round(ev.xdata), np.floor(hi)), np.ceil(lo)))
                self._canvas.draw_idle()

        def _release(self, ev):
            if self._dragging:
                self._dragging = False
                self.set_user_value("nShotOff", self.shot_line.get_xdata()[0])

        def _table_changed(self, item):
            if self.shot_line is not None and item.column() == 2 and PARAM_NAMES[item.row()] == "nShotOff":
                try:
                    self._set_shot(float(item.text()))
                    self._canvas.draw_idle()
                except ValueError:
                    pass

        def set_user_value(self, name, value):
            self.table.item(PARAM_NAMES.index(name), 2).setText(f"{float(value):g}")

        def user_values(self) -> list:
            out = []
            for i, name in enumerate(PARAM_NAMES):
                text = self.table.item(i, 2).text()
                try:
                    out.append(float(text))
                except ValueError:
                    raise ValueError(f"Metadata dialog: {name} = {text!r} is not a number") from None
            return out

    return MetadataDialog


def run(node, reconFoV, si=None):
    """Show the dialog and apply the result; on Cancel or close the extracted values are kept."""
    from monalisa._mat import disp
    from monalisa.imDisp._qt import run_dialog

    dlg = dialog_class()(node, reconFoV, si)
    if run_dialog(dlg):
        values = dlg.user_values()
        node, reconFoV = apply_values(node, reconFoV, values, dlg.case.currentText(),
                                      dlg.navigation.currentText() == "SI Navigation", dlg.roosk.isChecked())
        changed = [f"{n} = {v:g}" for n, v, e in zip(PARAM_NAMES, values, dlg.extracted, strict=True) if v != e]
        if changed:
            disp("Metadata changed by the user: " + ", ".join(changed))
        return node, reconFoV
    return apply_values(node, reconFoV, dlg.extracted, "Non-Cartesian")
