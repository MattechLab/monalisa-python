"""Port of src/sparseMat/m/bmSparseMat_completeMatlabSparse.m."""

import scipy.sparse as sp

from monalisa._mat import vec


def bmSparseMat_completeMatlabSparse(argSparse, mySize):
    """Pad a sparse matrix with empty rows/columns up to ``mySize``."""
    m = sp.csc_matrix(argSparse)
    b1, b2 = (int(s) for s in vec(mySize)[:2])
    a1, a2 = m.shape
    if b1 > a1 or b2 > a2:
        m = sp.csc_matrix((m.data, m.indices, m.indptr), shape=(max(a1, b1), a2))
        if b2 > a2:
            m = sp.hstack([m, sp.csc_matrix((m.shape[0], b2 - a2))], format="csc")
    return m
