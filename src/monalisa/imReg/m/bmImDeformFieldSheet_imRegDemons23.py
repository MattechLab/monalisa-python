"""Port of src/imReg/m/bmImDeformFieldSheet_imRegDemons23.m.

MATLAB's ``imregdemons`` is replaced by the open-source implementation of
``monalisa.imReg._demons`` (SimpleITK), validated on registration quality.
"""

import numpy as np

from monalisa._mat import cell_shape, isempty, new_cell, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.imReg._demons import imregdemons
from monalisa.imReg.m.bmImDeformFieldChain_imRegDemons23 import (
    _postprocess_field,
    _private_rescale,
    _private_smooth,
    _single,
)
from monalisa.readWrite._mat73 import savemat73

maxImVal = 255  # -------------------------------------------------------------- magic number

_SHEET_TYPES = ("curr_to_prev", "curr_to_next", "prev_to_curr", "next_to_curr")


def bmImDeformFieldSheet_imRegDemons23(x, n_u, sheet_type, nIter, nSmooth, arg_name,
                                       myMask=None, maxPixDisplacement=None, *, nargout=2):
    """Demons deformation fields along both dimensions of the sheet ``x`` (``nCell_1 x nCell_2`` cell).

    Like :func:`bmImDeformFieldChain_imRegDemons23`, for the neighbours along
    the first (``imDeformField_1``, ``nIter[0]`` iterations) and the second
    dimension (``imDeformField_2``, ``nIter[1]`` iterations), cyclically.
    Returns ``(imDeformField_1, imDeformField_2)`` and, with ``nargout=4``,
    the registered images ``(im_out_1, im_out_2)`` too. If ``arg_name`` is
    given, the four cells are saved to ``arg_name + '_1'``, ``'_2'``,
    ``'_im_out_1'`` and ``'_im_out_2'`` (v7.3 MAT-files).
    """
    sheet_type = str(np.asarray(sheet_type).item()) if not isinstance(sheet_type, str) else sheet_type
    nIter = vec(nIter)
    nIter_1, nIter_2 = int(nIter[0]), int(nIter[1])
    nSmooth = int(np.asarray(nSmooth).item())

    x = bmBlockReshape(x, n_u)
    nCell_1, nCell_2 = cell_shape(x)
    imDim = vec(n_u).size

    if not isempty(myMask):
        myMask = np.asarray(myMask)
        x = np.vectorize(lambda a: a * myMask, otypes=[object])(x)
        myMask = bmBlockReshape(np.repeat(myMask.reshape(-1, 1, order="F"), imDim, axis=1), n_u)

    if sheet_type not in _SHEET_TYPES:
        raise ValueError(" 'sheet_type' is unknown. ")

    im = new_cell((nCell_1, nCell_2))
    for i in range(nCell_1):
        for j in range(nCell_2):
            im[i, j] = _private_rescale(_single(_private_smooth(x[i, j], nSmooth)), maxImVal)

    imDeformField_1 = new_cell((nCell_1, nCell_2))
    imDeformField_2 = new_cell((nCell_1, nCell_2))
    im_out_1 = new_cell((nCell_1, nCell_2))
    im_out_2 = new_cell((nCell_1, nCell_2))
    for i in range(nCell_1):
        for j in range(nCell_2):
            i_minus_1 = (i - 1) % nCell_1
            i_plus_1 = (i + 1) % nCell_1
            j_minus_1 = (j - 1) % nCell_2
            j_plus_1 = (j + 1) % nCell_2
            curr = (i, j)
            (moving_1, fixed_1), (moving_2, fixed_2) = {
                "curr_to_prev": ((curr, (i_minus_1, j)), (curr, (i, j_minus_1))),
                "curr_to_next": ((curr, (i_plus_1, j)), (curr, (i, j_plus_1))),
                "prev_to_curr": (((i_minus_1, j), curr), ((i, j_minus_1), curr)),
                "next_to_curr": (((i_plus_1, j), curr), ((i, j_plus_1), curr)),
            }[sheet_type]

            v_reg_1, tmp_im_1 = imregdemons(im[moving_1][0], im[fixed_1][0], [nIter_1, nIter_1 // 2, nIter_1 // 4])
            _, min_1, max_1 = im[moving_1]
            v_reg_2, tmp_im_2 = imregdemons(im[moving_2][0], im[fixed_2][0], [nIter_2, nIter_2 // 2, nIter_2 // 4])
            _, min_2, max_2 = im[moving_2]

            im_out_1[i, j] = (tmp_im_1 * max_1 / np.float32(maxImVal) + min_1).astype(np.float32)
            im_out_2[i, j] = (tmp_im_2 * max_2 / np.float32(maxImVal) + min_2).astype(np.float32)
            imDeformField_1[i, j] = _postprocess_field(v_reg_1, n_u, myMask, maxPixDisplacement)
            imDeformField_2[i, j] = _postprocess_field(v_reg_2, n_u, myMask, maxPixDisplacement)

    if not isempty(arg_name):
        arg_name = str(np.asarray(arg_name).item()) if not isinstance(arg_name, str) else arg_name
        savemat73(arg_name + "_1.mat", {"imDeformField_1": imDeformField_1})
        savemat73(arg_name + "_2.mat", {"imDeformField_2": imDeformField_2})
        savemat73(arg_name + "_im_out_1.mat", {"im_out_1": im_out_1})
        savemat73(arg_name + "_im_out_2.mat", {"im_out_2": im_out_2})

    if nargout >= 4:
        return imDeformField_1, imDeformField_2, im_out_1, im_out_2
    return imDeformField_1, imDeformField_2
