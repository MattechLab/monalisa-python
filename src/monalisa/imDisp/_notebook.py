"""Slice viewer for Jupyter notebooks (ipywidgets + matplotlib), used by bmImage."""

from __future__ import annotations

import numpy as np

from monalisa.imDisp.bmImage import AXIS_LABELS

# view -> (sliced axis, row axis, column axis), as MATLAB's "Along X / Y / Z" permutations
VIEWS = {"along z": (2, 0, 1), "along y": (1, 2, 0), "along x": (0, 1, 2)}


class NotebookViewer:
    """Sliders for the slice and frame indices, a view selector (along x, y or z) and a contrast
    range. ``image()`` returns the 2D array currently shown."""

    def __init__(self, x: np.ndarray, name=None, contrast_limits=None):
        import ipywidgets as w

        self.x = x
        self.name = name
        nd = x.ndim
        lo, hi = (float(np.min(x)), float(np.max(x))) if contrast_limits is None else contrast_limits
        views = [v for v in VIEWS if nd >= 3] or ["along z"]
        self.view = w.Dropdown(options=views, value="along z", description="view")
        self.index = {k: w.IntSlider(min=1, max=x.shape[k], value=x.shape[k] // 2 + 1,
                                     description=AXIS_LABELS[k], continuous_update=False)
                      for k in range(nd)}
        step = (hi - lo) / 200 if hi > lo else 1.0
        self.contrast = w.FloatRangeSlider(min=lo, max=hi if hi > lo else lo + 1, value=(lo, hi), step=step,
                                           description="contrast", continuous_update=False, readout_format=".3g")
        self.out = w.Output()
        for c in (self.view, self.contrast, *self.index.values()):
            c.observe(lambda _: self.refresh(), names="value")
        self.widget = w.VBox([w.HBox([self.view, self.contrast]), *self._sliders(), self.out])
        self.view.observe(lambda _: self._relayout(), names="value")

    def _sliders(self):
        sliced = VIEWS[self.view.value][0] if self.x.ndim >= 3 else None
        return [s for k, s in self.index.items() if k >= 3 or k == sliced]

    def _relayout(self):
        self.widget.children = (self.widget.children[0], *self._sliders(), self.out)

    def image(self) -> np.ndarray:
        x = self.x
        if x.ndim == 2:
            return x
        k, r, c = VIEWS[self.view.value]
        idx = [slice(None)] * x.ndim
        idx[k] = self.index[k].value - 1
        for d in range(3, x.ndim):
            idx[d] = self.index[d].value - 1
        im = x[tuple(idx)]  # remaining axes in increasing order
        return im if r < c else im.T

    def title(self) -> str:
        parts = [self.name] if self.name else []
        if self.x.ndim >= 3:
            k = VIEWS[self.view.value][0]
            parts.append(f"{AXIS_LABELS[k]} = {self.index[k].value}/{self.x.shape[k]}")
        parts += [f"{AXIS_LABELS[d]} = {self.index[d].value}/{self.x.shape[d]}" for d in range(3, self.x.ndim)]
        return "   ".join(parts)

    def refresh(self):
        # a pyplot-free figure: display() renders it inline in Jupyter and never blocks
        from IPython.display import display
        from matplotlib.figure import Figure

        with self.out:
            self.out.clear_output(wait=True)
            fig = Figure(figsize=(5, 5))
            ax = fig.add_subplot()
            k, r, c = VIEWS[self.view.value] if self.x.ndim >= 3 else (None, 0, 1)
            ax.imshow(self.image(), cmap="gray", vmin=self.contrast.value[0], vmax=self.contrast.value[1])
            ax.set_ylabel(AXIS_LABELS[r])
            ax.set_xlabel(AXIS_LABELS[c])
            ax.set_title(self.title(), fontsize=9)
            display(fig)

    def show(self):
        from IPython.display import display

        display(self.widget)
        self.refresh()

    def _repr_mimebundle_(self, **kw):
        return self.widget._repr_mimebundle_(**kw)
