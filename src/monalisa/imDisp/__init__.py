"""Display and interactive tools (Python counterpart of upstream src/imDisp).

* :func:`~monalisa.imDisp.bmImage.bmImage`: 2D to 5D image viewer (napari window, or sliders in a
  Jupyter notebook), replacing MATLAB's ``bmImage``;
* :func:`~monalisa.imDisp.roipoly.roipoly`: polygon region of interest, like MATLAB ``roipoly``.

The interactive dialogs of the MATLAB code (metadata check, coil-mask thresholds and bounding
box) live next to the functions that open them, as upstream, and use the helpers of
``monalisa.imDisp._qt``. Every interactive step has a non-interactive equivalent (a parameter).
"""
