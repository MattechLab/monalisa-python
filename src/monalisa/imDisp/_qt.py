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
    "library libxcb-cursor is missing. Install it once, then restart Python / the kernel:\n"
    "    conda install -c conda-forge xcb-util-cursor   (in a conda environment, no admin rights)\n"
    "    sudo apt install libxcb-cursor0                (Debian, Ubuntu)\n"
    "    sudo dnf install xcb-util-cursor               (Fedora)\n"
    "In a notebook, bmImage(x, view='inline') works without it.")


def check_display(hint: str = "") -> None:
    """Raise a Python error (instead of a Qt abort, which kills the process or the Jupyter kernel)
    when Qt windows cannot be opened, and prepare Qt before it starts (see ``_avoid_gtk_theme``)."""
    if not has_display():
        raise NoDisplayError("This step needs a display for its window (none found). " + hint)
    if _needs_xcb() and not _has_xcb_cursor():
        raise NoDisplayError(XCB_CURSOR_HELP)
    _avoid_gtk_theme()
    _close_windows_at_exit()


def _avoid_gtk_theme() -> None:
    """In a conda environment, use Qt's built-in theme instead of its GTK3 theme plugin.

    The plugin (chosen by Qt on GNOME and similar desktops) loads the system GTK libraries, built
    for the system GLib and HarfBuzz, while conda packages (matplotlib >= 3.11 through libraqm)
    load the environment's own: whichever comes second breaks. Qt then segfaults when it starts
    after matplotlib has drawn a figure (in Jupyter: the kernel dies), or matplotlib fails to import
    after a window was opened. Only the look of the native dialogs changes (napari has its own
    style). A theme chosen with ``QT_QPA_PLATFORMTHEME`` is kept."""
    if not sys.platform.startswith("linux") or "QT_QPA_PLATFORMTHEME" in os.environ:
        return
    if os.path.exists(os.path.join(sys.prefix, "lib", "libglib-2.0.so.0")):
        os.environ["QT_QPA_PLATFORMTHEME"] = "generic"


_EXIT_HOOK = False


def _close_windows_at_exit() -> None:
    """Close the windows still open when Python exits while Qt is alive: left to the interpreter's
    teardown, their OpenGL canvases can be destroyed out of order (segfault on exit)."""
    global _EXIT_HOOK
    if _EXIT_HOOK:
        return
    _EXIT_HOOK = True
    import atexit

    def close_all():
        from qtpy.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None:
            app.closeAllWindows()
            app.processEvents()

    atexit.register(close_all)


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


_XCB_CURSOR = "libxcb-cursor.so.0"


def _has_xcb_cursor() -> bool:
    """libxcb-cursor (needed by Qt >= 6.5 for X11 windows) is available, from the system or, if
    missing there, from the conda environment (conda-forge package ``xcb-util-cursor``)."""
    from qtpy import QT_VERSION

    if tuple(int(v) for v in QT_VERSION.split(".")[:2]) < (6, 5):
        return True
    return _system_has_xcb_cursor() or _load_env_xcb_cursor()


def _system_has_xcb_cursor() -> bool:
    # Qt loads it from the system library paths or LD_LIBRARY_PATH. Not ctypes.util.find_library:
    # under conda it also searches the environment's lib folder, which Qt does not.
    import subprocess

    for d in os.environ.get("LD_LIBRARY_PATH", "").split(os.pathsep):
        if d and os.path.exists(os.path.join(d, _XCB_CURSOR)):
            return True
    for ldconfig in ("/sbin/ldconfig", "/usr/sbin/ldconfig", "ldconfig"):
        try:
            out = subprocess.run([ldconfig, "-p"], capture_output=True, text=True, timeout=10).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        return _XCB_CURSOR in out
    return True  # cannot tell: let Qt try


def _load_env_xcb_cursor() -> bool:
    """Load the conda environment's copy before Qt starts: Qt's platform plugin then uses it (a
    library already loaded under the same name is reused)."""
    import ctypes

    for prefix in dict.fromkeys(p for p in (sys.prefix, os.environ.get("CONDA_PREFIX")) if p):
        path = os.path.join(prefix, "lib", _XCB_CURSOR)
        if os.path.exists(path):
            try:
                ctypes.CDLL(path, mode=ctypes.RTLD_GLOBAL)
                return True
            except OSError:
                pass
    return False


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
