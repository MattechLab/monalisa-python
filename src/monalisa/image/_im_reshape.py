"""Port of src/image123/bmImReshape.m."""

from monalisa._mat import col
from monalisa.image._im_dim import im_dim


def im_reshape(argIm, nargout=3):
    """Image as column (1D) or unchanged, with ``(imDim, imSize, sx, sy, sz)``."""
    outIm = argIm
    imDim = int(im_dim(argIm, nargout=1))
    if imDim == 0:
        raise ValueError("The image dimension is 0. ")
    if imDim == 1:
        outIm = col(outIm)
    imDim, imSize, s1, s2, s3 = im_dim(outIm, nargout=5)
    return (outIm, imDim, imSize, s1, s2, s3)[: max(nargout, 1)]
