# Upstream issues found while porting

Behaviours of the MATLAB code that look unintended. The Python port reproduces them (parity first)
unless stated otherwise; they should be reported/fixed upstream and then in both code bases.

| Function | Issue | Python port |
|---|---|---|
| `fourier123/prep_function/bmK.m` | 1D case: `x_mask = (x < nWin_half) \| (x > nWin_half)` lacks the minus sign of the lower bound, so only `x == nWin_half` survives. 2D/3D use `-nWin_half`. | reproduced |
| `traj123/bmTraj_formatTraj.m` | When the trajectory has fewer than 2 points, `myDataFlag` is used before being defined (MATLAB error). | defined first (no error) |
| `traj123/bmTraj_norm.m` | `reshape(myNorm, mySize(1, 2:end))` errors in MATLAB for a 2-D trajectory `[imDim, nPt]` (size vector with one element). | returns `(nPt, 1)` |
| `gridding123/m/bmGridder_n2u_leight.m` + MEX | The MEX kernels always use a Gaussian kernel (`kernelParam(1)` as sigma), whatever `kernelType`; with `'kaiser'`, `bmMathilda` deapodizes with the Kaiser–Bessel kernel while gridding with a Gaussian of sigma = 1.95. | reproduced |
| `rawDataReader/siemens/dhSiemensReadMetaData.m` | `autoFlag = false` (used by the tutorial) opens metadata dialogs; batch use needs `autoFlag = true`. | n/a |
