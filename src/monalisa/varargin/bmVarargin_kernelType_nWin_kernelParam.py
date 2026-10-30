"""Port of src/varargin/bmVarargin_kernelType_nWin_kernelParam.m."""

import numpy as np

from monalisa._mat import double, isempty, single


def bmVarargin_kernelType_nWin_kernelParam(kernelType=None, nWin=None, kernelParam=None):
    """Fill in the default gridding kernel: ``'gauss'``, ``nWin = 3``,
    ``kernelParam = [0.61, 10]`` (gauss) or ``[1.95, 10, 10]`` (kaiser)."""
    if isempty(kernelType) or not isinstance(kernelType, str):
        kernelType = "gauss"
    if isempty(nWin):
        if kernelType in ("gauss", "kaiser"):
            nWin = 3.0
    if isempty(kernelParam):
        if kernelType == "gauss":
            kernelParam = np.array([[0.61, 10.0]])
        elif kernelType == "kaiser":
            kernelParam = np.array([[1.95, 10.0, 10.0]])
    nWin = double(single(nWin))
    kernelParam = double(single(kernelParam))
    if kernelType == "gauss" and np.size(kernelParam) == 3:
        raise ValueError("Wrong list of gridding kernel parameters. ")
    if kernelType == "kaiser" and np.size(kernelParam) == 2:
        raise ValueError("Wrong list of gridding kernel parameters. ")
    return kernelType, nWin, kernelParam
