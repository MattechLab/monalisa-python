"""Port of src/sparseMat/m/bmSparseMat_blockPartition.m."""

import numpy as np

from monalisa._mat import fix


def bmSparseMat_blockPartition(r_nJump, nJumpPerBlock_factor, blockLengthMax_factor, mode=None):
    """Partition the rows in blocks of bounded number of non-zeros.

    Returns ``(l_block_start, block_length, nBlock, zero_block_flag)``; with
    ``mode == 'one'`` a single block holds all rows.
    """
    r_nJump = np.ravel(r_nJump)
    if np.sum(r_nJump) <= 0:
        return None, None, None, True
    if mode == "one":
        return np.int32(0), np.int32(r_nJump.size), np.int32(1), False

    l_nJump = r_nJump.size
    r_nJump_max = float(np.max(r_nJump))
    nJumpPerBlock = int(fix(float(np.ravel(nJumpPerBlock_factor)[0]) * r_nJump_max) + 1)
    block_length_max = int(fix(float(np.ravel(blockLengthMax_factor)[0]) * r_nJump_max))
    r = r_nJump.astype(np.int64)

    starts, lengths = [], []
    zero_block_flag = False
    start_last = 0
    length_last = 0
    while True:
        start = start_last + length_last
        if not start < l_nJump:
            break
        length = 1
        ind_next = start + 1
        if ind_next < l_nJump:
            n2 = r[start]
            while ind_next < l_nJump:
                n2 = n2 + r[ind_next]
                if n2 < nJumpPerBlock and length < block_length_max:
                    length += 1
                    ind_next += 1
                else:
                    break
            if r[start : start + length].sum() <= 0:
                zero_block_flag = True
            starts.append(start)
            lengths.append(length)
            start_last, length_last = start, length
        else:
            if r[start : start + length].sum() <= 0:
                zero_block_flag = True
            starts.append(start)
            lengths.append(length)
            break
    l_block_start = np.array([starts], dtype=np.int32)
    block_length = np.array([lengths], dtype=np.int32)
    return l_block_start, block_length, np.int32(len(starts)), zero_block_flag
