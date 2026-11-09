"""Viewer and interactive dialogs, driven programmatically (off-screen Qt)."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np  # noqa: E402
import pytest  # noqa: E402

pytest.importorskip("pytestqt")

import monalisa as ml  # noqa: E402
import monalisa.imDisp._qt as qt  # noqa: E402
from monalisa.coilSense.automatic import _threshold_dialog, selectROI  # noqa: E402
from monalisa.imDisp import roipoly  # noqa: E402
from monalisa.imDisp.bmImage import image_data, view_order  # noqa: E402
from monalisa.mriRecon.class_.bmMriAcquisitionParam import bmMriAcquisitionParam  # noqa: E402
from monalisa.rawDataReader import _metadata_dialog  # noqa: E402


def accept_with(action=None):
    """A replacement for run_dialog that applies ``action(dlg)`` and confirms."""

    def run(dlg):
        if action is not None:
            action(dlg)
        return True

    return run


# --- bmImage -----------------------------------------------------------------------------------


def test_image_data_conversions():
    frames = [np.full((4, 5, 6), i, dtype=np.complex64) * (1 + 1j) for i in range(3)]
    x = image_data(frames)
    assert x.shape == (4, 5, 6, 3)
    np.testing.assert_allclose(x[0, 0, 0], np.abs(np.arange(3) * (1 + 1j)), rtol=1e-6)
    assert image_data(np.ones((3, 4), dtype=bool)).dtype == np.float64
    assert image_data(np.ones((3, 4, 1, 1))).shape == (3, 4)


def test_view_order_shows_matlab_slices():
    assert view_order(2) == (0, 1)
    assert view_order(3) == (2, 0, 1)
    assert view_order(5) == (4, 3, 2, 0, 1)


def test_bmImage_napari(qtbot):
    napari = pytest.importorskip("napari")
    viewer = napari.Viewer(show=False)
    try:
        x = np.random.default_rng(0).random((6, 7, 8, 2))
        v = ml.bmImage(x, viewer=viewer, name="x")
        assert v is viewer
        layer = viewer.layers["x"]
        assert layer.data.shape == (6, 7, 8, 2)
        assert viewer.dims.order == (3, 2, 0, 1)
        assert viewer.dims.displayed == (0, 1)
        assert tuple(viewer.dims.axis_labels) == ("x", "y", "z", "t")
    finally:
        viewer.close()


def _click(ov, view, position, drag=False):
    """Run the mouse callback of a slice view for a press / (move) / release at ``position``."""
    from types import SimpleNamespace

    model = ov.models[view]
    event = SimpleNamespace(button=1, type="mouse_press", position=position)
    gen = model.mouse_drag_callbacks[-1](model, event)
    next(gen)
    if drag:
        event.type = "mouse_move"
        next(gen)
    event.type = "mouse_release"
    with pytest.raises(StopIteration):
        next(gen)


def test_orthogonal_layout(qtbot):
    pytest.importorskip("napari")
    from monalisa.imDisp._ortho import OrthoViewer

    x = np.random.default_rng(0).random((10, 12, 14, 3))
    ov = OrthoViewer(x, name="x")
    try:
        assert {v: m.dims.displayed for v, m in ov.models.items()} == {
            "along z": (0, 1), "along x": (1, 2), "3D": (2, 0, 1), "along y": (2, 0)}
        assert ov.models["3D"].dims.ndisplay == 3
        assert ov.point == (5, 6, 7, 0)  # centre, first frame
        ov.set_point([2, 3, 4, 1])
        assert all(m.dims.current_step == (2, 3, 4, 1) for m in ov.models.values())
        ov.set_point([50, -3, 7, 2])  # clipped to the image
        assert ov.point == (9, 0, 7, 2)
        ov.models["along y"].dims.current_step = (2, 5, 4, 1)  # the slider of one view moves all
        assert ov.models["3D"].dims.current_step == (2, 5, 4, 1)
        # crosshair of "along z" (rows x, columns y): lines at x = 2 and y = 5, on slice z = 4, t = 1
        lines = [np.asarray(d) for d in ov.crosshairs["along z"].data]
        np.testing.assert_array_equal(lines[0], [[2, 0, 4, 1], [2, 11, 4, 1]])
        np.testing.assert_array_equal(lines[1], [[0, 5, 4, 1], [9, 5, 4, 1]])
        assert "x = 3 / 10" in ov.window.readout.text() and f"{x[2, 5, 4, 1]:.4g}" in ov.window.readout.text()
        # a click moves the two axes shown in that view; a drag (pan) does not move the cursor
        _click(ov, "along z", (7.2, 1.6, 0, 0))
        assert ov.point == (7, 2, 4, 1)
        _click(ov, "along x", (0, 10.4, 12.7, 0))
        assert ov.point == (7, 10, 13, 1)
        _click(ov, "along y", (1, 1, 1, 0), drag=True)
        assert ov.point == (7, 10, 13, 1)
        # contrast set in one view applies to all
        ov.images["along x"].contrast_limits = (0.2, 0.7)
        assert all(tuple(i.contrast_limits) == (0.2, 0.7) for i in ov.images.values())
        assert set(ov.qt_viewers["along z"].controls.widgets) == set(ov.models["along z"].layers)
    finally:
        ov.close()
    with pytest.raises(ValueError, match="3D"):
        OrthoViewer(np.zeros((4, 4)))
    with pytest.raises(ValueError, match="3D"):
        ml.bmImage(np.zeros((4, 4)), view="ortho")


def test_missing_xcb_cursor_is_a_python_error(monkeypatch):
    # Qt >= 6.5 aborts the process (and the Jupyter kernel) without libxcb-cursor0
    from monalisa.imDisp import _qt

    monkeypatch.setattr(_qt, "_needs_xcb", lambda: True)
    monkeypatch.setattr(_qt, "_has_xcb_cursor", lambda: False)
    with pytest.raises(_qt.NoDisplayError, match="libxcb-cursor0"):
        ml.bmImage(np.zeros((4, 4, 4)), view="window")


def test_bmImage_render3d(qtbot):
    napari = pytest.importorskip("napari")
    viewer = napari.Viewer(show=False)
    try:
        x = np.random.default_rng(0).random((6, 7, 8, 2))
        ml.bmImage(x, "3d", viewer=viewer, name="x")
        assert viewer.dims.ndisplay == 3
        assert viewer.dims.displayed == (2, 0, 1)  # volume of x, y, z; slider on t
    finally:
        viewer.close()
    with pytest.raises(ValueError, match="unknown view"):
        ml.bmImage(x, view="3D slices")
    with pytest.raises(ValueError, match="viewer="):
        ml.bmImage(x, view="inline", viewer=viewer)


def test_bmImage_old_keywords(qtbot):
    napari = pytest.importorskip("napari")
    viewer = napari.Viewer(show=False)
    try:
        x = np.random.default_rng(0).random((6, 7, 8))
        with pytest.warns(FutureWarning, match="view='3d', contrast=\\(low, high\\)"):
            ml.bmImage(x, viewer=viewer, render3d=True, contrast_limits=(0.1, 0.9))
        assert viewer.dims.ndisplay == 3
        assert tuple(viewer.layers[-1].contrast_limits) == (0.1, 0.9)
    finally:
        viewer.close()
    with pytest.raises(TypeError, match="colour"):
        ml.bmImage(x, colour="red")


def test_notebook_viewer_slices():
    pytest.importorskip("ipywidgets")
    from monalisa.imDisp._notebook import NotebookViewer

    x = np.arange(4 * 5 * 6 * 2, dtype=float).reshape(4, 5, 6, 2)
    w = NotebookViewer(x)
    w.index[2].value, w.index[3].value = 3, 2
    np.testing.assert_array_equal(w.image(), x[:, :, 2, 1])
    w.view.value = "along y"
    w.index[1].value = 4
    np.testing.assert_array_equal(w.image(), x[:, 3, :, 1].T)  # rows z, columns x
    w.view.value = "along x"
    w.index[0].value = 1
    np.testing.assert_array_equal(w.image(), x[0, :, :, 1])  # rows y, columns z


# --- roipoly -----------------------------------------------------------------------------------


def test_roipoly_from_vertices():
    m = ml.roipoly(np.zeros((10, 12)), [3, 8, 8, 3], [2, 2, 5, 5])  # columns 3..8, rows 2..5
    expected = np.zeros((10, 12), dtype=bool)
    expected[1:5, 2:8] = True
    np.testing.assert_array_equal(m, expected)


def test_roipoly_dialog(qtbot, monkeypatch):
    monkeypatch.setattr(roipoly, "run_dialog", accept_with(lambda d: (d.set_vertices([3, 8, 8, 3], [2, 2, 5, 5]),
                                                                       d.confirm())))
    m = ml.roipoly(np.random.default_rng(1).random((10, 12)))
    assert m.sum() == 24 and m[1:5, 2:8].all()


# --- metadata dialogs --------------------------------------------------------------------------


def _node():
    n = bmMriAcquisitionParam(None)
    n.N, n.nLine, n.nShot, n.nSeg, n.nCh, n.nEcho, n.nShot_off = 480.0, 2200.0, 100.0, 22.0, 1.0, 1.0, 13.0
    n.FoV = np.array([[480.0]])
    n.selfNav_flag, n.roosk_flag = True, False
    return n


def test_mode_matches_matlab():
    assert _metadata_dialog.mode([3, 1, 3, 1]) == 1  # tie: smallest
    assert _metadata_dialog.mode([[240, 240, 300]]) == 240


def test_metadata_confirm_and_cancel(qtbot, monkeypatch):
    si = (np.random.default_rng(2).random((480, 100)), np.ones((1, 100)), np.ones((1, 100)))

    def edit(dlg):
        dlg.set_user_value("FoV (recon)", 240)
        dlg._set_shot(20)  # drag the steady-state line to shot 20
        dlg._dragging = True
        dlg._release(None)
        dlg.roosk.setChecked(True)

    monkeypatch.setattr(qt, "run_dialog", accept_with(edit))
    node, reconFoV = ml.checkMetadataInteractive(*si, _node(), np.array([[480.0]]))
    assert node.nShot_off == 20 and node.roosk_flag
    np.testing.assert_array_equal(reconFoV, [[240.0]])
    np.testing.assert_array_equal(node.FoV, [[480.0]])

    monkeypatch.setattr(qt, "run_dialog", lambda dlg: False)  # Cancel: extracted values
    node, reconFoV = ml.correctMetadataInteractive(_node(), np.array([[480.0]]))
    assert node.nShot_off == 13 and not node.roosk_flag
    np.testing.assert_array_equal(reconFoV, [[480.0]])


# --- coil mask: thresholds and bounding box ----------------------------------------------------


def _phantom(N=24):
    g = np.arange(N) - N / 2
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    rng = np.random.default_rng(3)
    obj = ((X / 8) ** 2 + (Y / 6) ** 2 + (Z / 7) ** 2 <= 1) * 80.0
    return obj + rng.random(obj.shape) * 10


def test_threshold_dialog(qtbot):
    data = _phantom()
    dlg = _threshold_dialog.dialog_class()(100, data, data, 30, 40)
    qtbot.addWidget(dlg)
    dlg.set_threshold("RMS", 123.4)  # clipped to colorMax - 1
    assert dlg.th["RMS"] == 99
    dlg.set_slice(25)  # wraps around
    assert dlg.curImNum == 1
    dlg.set_view("Along X")
    expected = np.transpose(data, (1, 2, 0))[:, :, 0].copy()
    expected[expected <= 40] = 0
    np.testing.assert_array_equal(dlg.slice("MIP"), expected)


def test_threshold_interactive_returns_choice(qtbot, monkeypatch):
    data = _phantom()
    auto = ml.thresholdRMS_MIP(100, data, data, [24, 24, 24], True)
    monkeypatch.setattr(qt, "run_dialog", accept_with(lambda d: d.set_threshold("MIP", 50)))
    th = ml.thresholdRMS_MIP(100, data, data, [24, 24, 24], False)
    assert th == (auto[0], 50.0)
    monkeypatch.setattr(qt, "run_dialog", lambda d: False)  # closed: automatic thresholds
    assert ml.thresholdRMS_MIP(100, data, data, [24, 24, 24], False) == auto


def test_select_roi(qtbot, monkeypatch):
    data = _phantom()
    N_u = [24, 24, 24]
    box = np.array([[3.0, 10], [4, 12], [5, 14]])

    def edit(dlg):
        dlg.set_edge(0, 0, 6.5)  # typed xMin
        view, sel = dlg.selectors[5]  # MIP along z: columns y, rows x
        assert view == "Along Z" and sel.extents == (4, 16, 6.5, 13)

    monkeypatch.setattr(selectROI, "run_dialog", accept_with(edit))
    coords = ml.selectROI(data, data, N_u, False, box)
    expected = selectROI.border_extraction([[6.5, 13], [4, 16], [5, 19]], N_u)
    np.testing.assert_array_equal(coords, expected)
    monkeypatch.setattr(selectROI, "run_dialog", lambda d: False)
    np.testing.assert_array_equal(ml.selectROI(data, data, N_u, False, box), [[3, 13], [4, 16], [5, 19]])


def test_mask_automatic_interactive_unchanged_equals_automatic(qtbot, monkeypatch):
    rng = np.random.default_rng(4)
    N = 24
    n = rng.normal(size=(3, 4000))
    t = n / np.linalg.norm(n, axis=0) * rng.uniform(-N / 2, N / 2, 4000) / N  # dK = 1 / N
    t = t.reshape(3, 40, 100)
    N_u, dK_u = np.array([[N, N, N]], float), np.full((1, 3), 1.0 / N)
    Gn = ml.bmTraj2SparseMat(t, np.ones((1, 4000)), N_u, dK_u, nargout=1)
    x = _phantom(N).astype(np.complex64)
    k = np.reshape(t, (3, -1), order="F") * N
    g = np.arange(N) - N / 2
    E = np.exp(-2j * np.pi * (np.einsum("ip,a->pa", k[:1], g)[:, :, None, None]
                              + np.einsum("ip,b->pb", k[1:2], g)[:, None, :, None]
                              + np.einsum("ip,c->pc", k[2:3], g)[:, None, None, :]) / N)
    y = np.einsum("pabc,abc->p", E, x)[:, None] * np.array([[1.0, 0.8, 0.6]])
    y = y.astype(np.complex64)

    shown, boxes = [], []
    monkeypatch.setattr("monalisa.imDisp.bmImage.bmImage", lambda im, **kw: shown.append(kw["name"]))
    monkeypatch.setattr(qt, "run_dialog", accept_with())
    monkeypatch.setattr(selectROI, "run_dialog", accept_with(lambda d: boxes.append(d.edges)))
    m_int = ml.bmCoilSense_nonCart_mask_automatic(y, Gn, False)
    assert shown == ["RMS", "MIP", "mask"]
    # the values confirmed in the windows, passed as parameters, give the same mask without windows
    th = ml.thresholdRMS_MIP(100, *_rms_mip(y, Gn), N_u, True)
    borders = selectROI.border_extraction(boxes[0], N_u.ravel())
    m_code = ml.bmCoilSense_nonCart_mask_automatic(y, Gn, True, th[0], th[1], borders)
    np.testing.assert_array_equal(m_int, m_code)
    assert 0 < m_code.sum() < m_code.size


def _rms_mip(y, Gn):
    from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape

    N_u = Gn.N_u.ravel()
    x = bmBlockReshape(ml.bmNasha(y, Gn, N_u), N_u)
    rms, mip = ml.bmRMS(x, N_u), ml.bmMIP(x, N_u)
    return 100 * (rms - rms.min()) / rms.max(), 100 * (mip - mip.min()) / mip.max()
