"""Port of src/sparseMat/m/bmSparseMat_r_nJump2index.m (+ MEX)."""

import numpy as np


def sparse_mat_r_n_jump_to_index(r_nJump):
    """1-based row index of every non-zero, given the number of non-zeros per row (int32 row)."""
    r_nJump = np.ravel(r_nJump, order="F").astype(np.int64)
    out = np.repeat(np.arange(r_nJump.size, dtype=np.int32), r_nJump) + np.int32(1)
    return out[None, :]
