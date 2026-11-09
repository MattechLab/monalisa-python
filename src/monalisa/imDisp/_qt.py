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


XCB_CURSOR_HELP = (
    "Qt (used for the napari window and the interactive steps) cannot open windows: the system "
    "library libxcb-cursor0 is missing. Install it once, then restart Python / the kernel:\n"
    "    sudo apt install libxcb-cursor0      (Debian, Ubuntu)\n"
    "    sudo dnf install xcb-util-cursor     (Fedora)\n"
    "In a notebook, bmImage(...) without render3d / backend='napari' works without it.")


def check_display(hint: str = "") -> None:
    """Raise a Python error (instead of a Qt abort, which kills the process or the Jupyter kernel)
    when Qt windows cannot be opened."""
    if not has_display():
        raise NoDisplayError("This step needs a display for its window (none found). " + hint)
    if _needs_xcb() and not _has_xcb_cursor():
        raise NoDisplayError(XCB_CURSOR_HELP)


def _needs_xcb() -> bool:
    """True when Qt will use its X11 (xcb) platform plugin: Linux, not Wayland, not off-screen."""
    if not sys.platform.startswith("linux"):
        return False
    from qtpy.QtWidgets import QApplication

    if QApplication.instance() is not None:  # Qt already running: the platform plugin is loaded
        return False
    platform = os.environ.get("QT_QPA_PLATFORM", "")
    if platform:
        return platform.split(":")[0].split(";")[0] == "xcb"
    return not os.environ.get("WAYLAND_DISPLAY")


def _has_xcb_cursor() -> bool:
    # Needed by Qt >= 6.5 and loaded from the system library paths or LD_LIBRARY_PATH (not from a
    # conda environment's lib folder, which ctypes.util.find_library also searches under conda).
    import subprocess

    from qtpy import QT_VERSION

    if tuple(int(v) for v in QT_VERSION.split(".")[:2]) < (6, 5):
        return True
    name = "libxcb-cursor.so.0"
    for d in os.environ.get("LD_LIBRARY_PATH", "").split(os.pathsep):
        if d and os.path.exists(os.path.join(d, name)):
            return True
    for ldconfig in ("/sbin/ldconfig", "/usr/sbin/ldconfig", "ldconfig"):
        try:
            out = subprocess.run([ldconfig, "-p"], capture_output=True, text=True, timeout=10).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        return name in out
    return True  # cannot tell: let Qt try


def qt_app(hint: str = ""):
    """The running QApplication, created if needed."""
    check_display(hint)
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
