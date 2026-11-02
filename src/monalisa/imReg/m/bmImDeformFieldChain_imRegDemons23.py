"""Port of src/imReg/m/bmImDeformFieldChain_imRegDemons23.m.

MATLAB's ``imregdemons`` is replaced by the open-source implementation of
``monalisa.imReg._demons`` (SimpleITK), validated on registration quality.
"""

import numpy as np

from monalisa._mat import cell_items, isempty, msize, new_cell, scalar, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.arrayUtility.bmPermuteToPoint import bmPermuteToPoint
from monalisa.image2.m.bmImDeformField_hardThresholding2 import bmImDeformField_hardThresholding2
from monalisa.imReg._demons import imregdemons
from monalisa.readWrite._mat73 import savemat73

maxImVal = 255  # ----------------------------------------- magic number

_CHAIN_TYPES = ("curr_to_prev", "curr_to_next", "prev_to_curr", "next_to_curr", "curr_to_first", "first_to_curr")


def bmImDeformFieldChain_imRegDemons23(x, n_u, chain_type, nIter, nSmooth, arg_name,
                                       myMask=None, maxPixDisplacement=None, *, nargout=1):
    """Demons deformation fields between the frames of the chain ``x``.

    ``chain_type`` says which frame is registered to which (``'curr_to_prev'``:
    the field warping frame ``i`` onto frame ``i-1``, cyclically, etc.). Each
    frame is smoothed ``nSmooth`` times and rescaled to ``[0, 255]`` before a
    3-level demons registration with ``[nIter, fix(nIter/2), fix(nIter/4)]``
    iterations. The fields are masked by ``myMask``, clipped to
    ``maxPixDisplacement`` pixels (2D) and returned in point format
    ``[imDim, nPt]``. With ``nargout=2`` the registered images are returned
    too. If ``arg_name`` is given, the fields are saved to ``arg_name`` and the
    images to ``arg_name + '_im_out'`` (v7.3 MAT-files).
    """
    chain_type = str(np.asarray(chain_type).item()) if not isinstance(chain_type, str) else chain_type
    if chain_type not in _CHAIN_TYPES:
        raise ValueError("bmImDeformField_thirdPart : 'chain_type' is unknown. ")
    nIter = int(scalar(nIter))
    nSmooth = int(scalar(nSmooth))
    iterations = [nIter, nIter // 2, nIter // 4]

    x = [np.asarray(xi) for xi in cell_items(bmBlockReshape(x, n_u))]
    imDim = vec(n_u).size
    nCell = len(x)

    if not isempty(myMask):
        myMask = np.asarray(myMask)
        x = [xi * myMask for xi in x]
        myMask = bmBlockReshape(np.repeat(np.asarray(myMask).reshape(-1, 1, order="F"), imDim, axis=1), n_u)

    # smoothed and rescaled frames (MATLAB recomputes them at every iteration, with the same result)
    im = [_private_rescale(_single(_private_smooth(xi, nSmooth)), maxImVal) for xi in x]

    imDeformField = new_cell((nCell, 1))
    im_out = new_cell((nCell, 1))
    for i in range(nCell):
        i_minus_1 = (i - 1) % nCell
        i_plus_1 = (i + 1) % nCell
        pair = {
            "curr_to_prev": (i, i_minus_1),
            "curr_to_next": (i, i_plus_1),
            "prev_to_curr": (i_minus_1, i),
            "next_to_curr": (i_plus_1, i),
            "curr_to_first": (i, 0),
            "first_to_curr": (0, i),
        }[chain_type]
        if chain_type in ("curr_to_first", "first_to_curr") and i == 0:
            # upstream: v_reg = [] and tmp_im undefined at the first frame (see docs/upstream_issues.md)
            continue
        moving, fixed = pair
        v_reg, tmp_im = imregdemons(im[moving][0], im[fixed][0], iterations)
        _, min_m, max_m = im[moving]
        im_out[i, 0] = (tmp_im * max_m / np.float32(maxImVal) + min_m).astype(np.float32)
        imDeformField[i, 0] = _postprocess_field(v_reg, n_u, myMask, maxPixDisplacement)

    if not isempty(arg_name):
        arg_name = str(np.asarray(arg_name).item()) if not isinstance(arg_name, str) else arg_name
        savemat73(arg_name if arg_name.endswith(".mat") else arg_name + ".mat", {"imDeformField": imDeformField})
        savemat73(arg_name + "_im_out.mat", {"im_out": im_out})

    if nargout >= 2:
        return imDeformField, im_out
    return imDeformField


def _postprocess_field(v_reg, n_u, myMask, maxPixDisplacement):
    """MATLAB [x, y(, z)] field -> masked, clipped field in point format, components in array-axis order."""
    v_reg = _private_flip_x_y(np.squeeze(v_reg))
    v_reg = bmBlockReshape(v_reg, n_u)
    if not isempty(myMask):
        v_reg = v_reg * myMask
    if not isempty(maxPixDisplacement):
        v_reg = bmImDeformField_hardThresholding2(v_reg, n_u, maxPixDisplacement)
    return bmPermuteToPoint(v_reg, n_u)


def _single(a):
    a = np.asarray(a)
    return a.astype(np.complex64 if np.iscomplexobj(a) else np.float32)


def _private_flip_x_y(v_in):
    v_out = np.squeeze(v_in)
    temp_size = msize(v_out)
    temp_N_u = list(temp_size[:-1])
    v_out = np.array(bmColReshape(v_out, temp_N_u))
    v_out[:, [0, 1]] = v_out[:, [1, 0]]
    return bmBlockReshape(v_out, temp_N_u)


def _private_smooth(im_in, nSmooth):
    im_out = np.asarray(im_in)
    imDim = im_out.ndim
    for _ in range(nSmooth):
        acc = im_out
        for ax in range(imDim):
            acc = acc + np.roll(im_out, 1, axis=ax)
        for ax in range(imDim):
            acc = acc + np.roll(im_out, -1, axis=ax)
        im_out = acc / (2 * imDim + 1)
    return im_out


def _private_rescale(arg_im, arg_val):
    out = np.abs(arg_im)
    out_min = out.min()
    out = out - out_min
    out_max = out.max()
    out = out / out_max
    out = out * np.float32(arg_val)
    return out, out_min, out_max

