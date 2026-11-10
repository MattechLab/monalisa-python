"""Image viewers (napari windows, sliders in Jupyter notebooks) and polygon masks.

The interactive dialogs of the MATLAB code (metadata check, coil-mask thresholds and
bounding box) live next to the functions that open them and use the helpers of
``monalisa.display._qt``. Every interactive step has a non-interactive equivalent
(a parameter).
"""

from monalisa.display._roipoly import poly2mask, roipoly
from monalisa.display._show_image import show_image

__all__ = [
    "poly2mask",
    "roipoly",
    "show_image",
]
