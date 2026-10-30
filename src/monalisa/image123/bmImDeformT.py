"""Port of src/image123/bmImDeformT.m."""

from monalisa._mat import isempty, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.arrayUtility.bmIsBlockShape import bmIsBlockShape
from monalisa.fourier1.bmDFT1_conjTrans import bmDFT1_conjTrans
from monalisa.fourier1.bmIDF1_conjTrans import bmIDF1_conjTrans
from monalisa.fourier2.bmDFT2_conjTrans import bmDFT2_conjTrans
from monalisa.fourier2.bmIDF2_conjTrans import bmIDF2_conjTrans
from monalisa.fourier3.bmDFT3_conjTrans import bmDFT3_conjTrans
from monalisa.fourier3.bmIDF3_conjTrans import bmIDF3_conjTrans
from monalisa.sparseMat.m.bmSparseMat_vec import bmSparseMat_vec


def bmImDeformT(Tut, x, n_u, K=None):
    """Adjoint of ``bmImDeform`` (``Tut`` is the transposed deformation matrix)."""
    if isempty(Tut):
        return x
    n_u = vec(n_u)
    imDim = n_u.size
    x_out = bmColReshape(x, n_u)
    if not isempty(K):
        K = bmColReshape(K, n_u)
        idfT, dftT = {1: (bmIDF1_conjTrans, bmDFT1_conjTrans), 2: (bmIDF2_conjTrans, bmDFT2_conjTrans),
                      3: (bmIDF3_conjTrans, bmDFT3_conjTrans)}[imDim]
        x_out = dftT(idfT(x_out, n_u, 1.0 / n_u) * K, n_u, 1.0 / n_u)
    x_out = bmSparseMat_vec(Tut, x_out, "omp", "complex", False)
    if bmIsBlockShape(x, n_u):
        x_out = bmBlockReshape(x_out, n_u)
    return x_out
