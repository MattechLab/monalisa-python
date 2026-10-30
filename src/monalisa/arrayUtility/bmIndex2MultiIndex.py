"""Port of src/arrayUtility/bmIndex2MultiIndex.m."""

import numpy as np

from monalisa._mat import fix, vec


def bmIndex2MultiIndex(argInd, argSize):
    """1-based linear index -> 1-based multi-index (row of doubles), column-major."""
    myInd = float(np.asarray(argInd).item()) - 1
    mySize = np.concatenate([[1.0], vec(argSize)])
    L = mySize.size - 1
    P = np.array([np.prod(mySize[: i + 1]) for i in range(L)])
    outInd = np.zeros((1, L))
    for i in range(L):
        k = L - 1 - i
        temp_ind = fix(myInd / P[k])
        outInd[0, k] = temp_ind
        myInd = myInd - temp_ind * P[k]
    return outInd + 1
