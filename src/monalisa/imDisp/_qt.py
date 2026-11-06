"""Qt helpers shared by the viewer and the interactive dialogs.

The dialogs are modal (``exec``), like MATLAB's ``uiwait``: the calling code waits until the user
confirms or closes the window. They work from scripts, IPython and Jupyter, as long as a display
is available.
"""

from __future__ import annotations

import os
import sys


class NoDisplayError(RuntimeError):
    """An interactive step was requested but no display is available."""


def has_display() -> bool:
    if os.environ.get("QT_QPA_PLATFORM", "") in ("offscreen", "minimal"):
        return True
    if sys.platform.startswith("linux"):
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return True


def qt_app(hint: str = ""):
    """The running QApplication, created if needed."""
    if not has_display():
        raise NoDisplayError("This interactive step needs a display (none found). " + hint)
    from qtpy.QtWidgets import QApplication

    global _APP
    app = QApplication.instance()
    if app is None:
        app = _APP = QApplication([])  # keep a reference: a collected QApplication crashes Qt
    return app


_APP = None


def run_dialog(dlg) -> bool:
    """Show ``dlg`` modally; True if the user confirmed."""
    from qtpy.QtWidgets import QDialog

    return dlg.exec() == QDialog.DialogCode.Accepted


def mpl_canvas(width: float, height: float):
    """A matplotlib figure embedded in a Qt widget: ``(figure, canvas)``."""
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.figure import Figure

    fig = Figure(figsize=(width, height), layout="constrained")
    return fig, FigureCanvasQTAgg(fig)


def in_jupyter() -> bool:
    try:
        from IPython import get_ipython
    except ImportError:
        return False
    shell = get_ipython()
    return shell is not None and shell.__class__.__name__ == "ZMQInteractiveShell"
