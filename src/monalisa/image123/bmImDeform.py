"""Port of src/image123/bmImDeform.m."""


from monalisa._mat import isempty, vec
from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape
from monalisa.arrayUtility.bmColReshape import bmColReshape
from monalisa.arrayUtility.bmIsBlockShape import bmIsBlockShape
from monalisa.fourier1.bmDFT1 import bmDFT1
from monalisa.fourier1.bmIDF1 import bmIDF1
from monalisa.fourier2.bmDFT2 import bmDFT2
from monalisa.fourier2.bmIDF2 import bmIDF2
from monalisa.fourier3.bmDFT3 import bmDFT3
from monalisa.fourier3.bmIDF3 import bmIDF3
from monalisa.sparseMat.m.bmSparseMat_vec import bmSparseMat_vec


def bmImDeform(Tu, x, n_u, K=None):
    """Apply the deformation matrix ``Tu`` to the images ``x`` (identity when ``Tu``
    is empty); with ``K`` the deformed images are filtered in k-space."""
    if isempty(Tu):
        return x
    n_u = vec(n_u)
    imDim = n_u.size
    x_out = bmSparseMat_vec(Tu, bmColReshape(x, n_u), "omp", "complex", False)
    if not isempty(K):
        K = bmColReshape(K, n_u)
        dft, idf = {1: (bmDFT1, bmIDF1), 2: (bmDFT2, bmIDF2), 3: (bmDFT3, bmIDF3)}[imDim]
        x_out = idf(dft(x_out, n_u, 1.0 / n_u) * K, n_u, 1.0 / n_u)
    if bmIsBlockShape(x, n_u):
        x_out = bmBlockReshape(x_out, n_u)
    return x_out
