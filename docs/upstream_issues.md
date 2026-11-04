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
| `optim/bmBackGradient_nT.m` | Not the exact adjoint of `bmBackGradient_n`: it computes `(P x - circshift(x, -1)) / dX` instead of `(P x - circshift(P x, -1)) / dX` (P zeroes the first slice), so `<G x, y> ≠ <x, Gᵀ y>` by the wrap-around slice (15 % on random 8×6×4 data; negligible for images with empty borders). | reproduced |
| `mathOp/bmNorm.m` | Calls itself (`sqrt(bmNorm(x, H))`): infinite recursion; probably meant `sqrt(bmSquaredNorm(x, H))`. | not ported (outside the demo scope) |
| `coilSense/nonCart/bmCoilSense_nonCart_mask_automatic.m` | The second column of `borders` returned by `detectROI` is a width but is used as an upper index; the upper y/z cuts use `borders(k,2):end` and the lower z cut `1:borders(3,1)` (off by one compared with x). | reproduced |
| `traj3/bmTraj_fullRadial3_phyllotaxis_lineAssym2.m` | With the 6-argument call, `flagExcludeSI` is undefined (MATLAB error when used). | no exclusion in that case |
| `image123/bmImZeroFill.m` | 1D branch reads the undefined variable `u`. | raises like MATLAB |
| `coilSense` / tutorial 1 | `bmCoilSense_nonCart_mask_automatic(y, Gn, false)` (as in the tutorial script) opens interactive windows and blocks in batch mode (`uiwait`). | `autoFlag = True` required |
| `imReg/m/bmImDeformFieldChain_imRegDemons23.m` | With `chain_type` `'curr_to_first'` or `'first_to_curr'`, the first frame sets `v_reg = []` but then reads `tmp_im`, which is not defined yet (MATLAB error at the first frame). | first field and image are `None` |
| `demo/script_demo/script_tutorial_1/*.m`, `docs/rst/1-2_installation.rst` | Only `src/` is added to the path (`addpath(genpath(srcDir))`), but the Siemens reader calls `mapVBVD_JH_for_monalisa` from `third_part/twix_for_monalisa`: on a clean MATLAB path the tutorial stops with "Undefined function 'mapVBVD_JH_for_monalisa'". The scripts also locate themselves with `matlab.desktop.editor.getActiveFilename`, so they only run from the Editor (not `run(...)` or `matlab -batch`). | n/a (Python package) |
| `demo/script_demo/script_tutorial_1/mitosius_script.m` | The normalization image is gridded with `dK_u = [1, 1, 1] / 384`, while the reconstructions use `1 / FoV` (FoV = 240 mm for the tutorial data). Only the normalization constant changes (all images scaled by the same factor), but 384 looks like a leftover from another protocol. | reproduced |
