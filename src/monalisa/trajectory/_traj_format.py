"""Port of src/traj123/bmTraj_formatTraj.m."""

import numpy as np

from monalisa.array._point_reshape import point_reshape


def traj_format(argTraj, argData=None, nargout=1):
    """Merge all k-space center points of a trajectory into a single point.

    Returns ``formatedTraj`` or ``(formatedTraj, formatedData, formatedIndex,
    formatedWeight)`` truncated to ``nargout``. ``formatedIndex`` holds
    1-based MATLAB indices (as doubles) into ``formatedTraj``.
    """
    argTraj = np.asarray(point_reshape(argTraj))
    myDataFlag = argData is not None
    if argTraj.shape[1] < 2:
        out = [argTraj, argData if myDataFlag else None, 1.0, 1.0]
        return out[0] if nargout <= 1 else tuple(out[:nargout])

    myEps = 10 * np.finfo(np.float64).eps
    imDim, nPt = argTraj.shape
    if myDataFlag:
        argData = np.asarray(point_reshape(argData))

    myNorm = np.zeros(nPt, dtype=argTraj.dtype)
    for i in range(imDim):
        myNorm = myNorm + argTraj[i, :] ** 2
    myNorm = np.sqrt(myNorm)
    myCenterMask = myNorm < myEps
    nPointCenter = int(np.sum(myCenterMask))
    if nPointCenter > 0:
        formatedTraj = np.concatenate(
            [np.zeros((imDim, 1), dtype=argTraj.dtype), argTraj[:, ~myCenterMask]], axis=1
        )
    else:
        formatedTraj = argTraj
    out = [formatedTraj]
    if nargout <= 1:
        return formatedTraj

    if myDataFlag:
        if nPointCenter > 0:
            myCenterData = np.mean(argData[:, myCenterMask], axis=1, keepdims=True)
            formatedData = np.concatenate([myCenterData, argData[:, ~myCenterMask]], axis=1)
        else:
            formatedData = argData
        out.append(formatedData)
    else:
        out.append(None)

    if nargout > 2:
        start = 1 if nPointCenter > 0 else 0
        idx = start + np.cumsum(~myCenterMask)
        formatedIndex = np.where(myCenterMask, 1, idx).astype(np.float64)[None, :]
        test = formatedTraj[:, formatedIndex[0].astype(np.int64) - 1]
        if np.max(np.abs(test - argTraj)) > myEps:
            raise RuntimeError("Something went wrong with formatedIndex in 'bmFormatTraj'. ")
        out.append(formatedIndex)
    if nargout > 3:
        formatedWeight = np.ones((1, nPt))
        if nPointCenter > 0:
            formatedWeight[0, myCenterMask] = 1 / nPointCenter
        out.append(formatedWeight)
    return tuple(out[:nargout])
