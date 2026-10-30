"""Port of src/sparseMat/m/bmSparseMat.m (handle class)."""

from __future__ import annotations

import numpy as np

from monalisa._mat import disp, isempty

_FIELDS = (
    "r_size", "r_ind", "r_jump", "r_nJump", "m_val", "l_size", "l_ind", "l_jump", "l_nJump",
    "nBlock", "block_length", "l_block_start", "m_block_start", "N_u", "d_u", "kernel_type",
    "nWin", "kernelParam", "block_type", "type", "l_squeeze_flag", "check_flag",
)


def _row(a, dtype):
    return np.reshape(np.asarray(a, dtype=dtype), (1, -1), order="F")


def _size2(a) -> int:
    return 0 if a is None else int(np.size(a))


class bmSparseMat:
    """Sparse matrix in Monalisa's row-compressed format.

    Rows are the *left* (``l``) side, columns the *right* (``r``) side. For
    each row ``r_nJump`` holds its number of non-zeros; their column indices
    are ``r_ind`` (1-based, type ``'matlab_ind'``) or, once ``cpp_prepare``
    has run, the jumps ``r_jump`` between consecutive non-zeros (absolute
    0-based index at the start of each block). ``l_squeeze`` removes empty
    rows; their positions are then kept in ``l_ind`` / ``l_jump``.
    Values ``m_val`` are single precision.
    """

    def __init__(self):
        self.r_size = None
        self.r_ind = None
        self.r_jump = None
        self.r_nJump = None
        self.m_val = None
        self.l_size = None
        self.l_ind = None
        self.l_jump = None
        self.l_nJump = None
        self.nBlock = None
        self.block_length = None
        self.l_block_start = None
        self.m_block_start = None
        self.N_u = None
        self.d_u = None
        self.kernel_type = "void"
        self.nWin = None
        self.kernelParam = None
        self.block_type = "void"
        self.type = "void"
        self.l_squeeze_flag = False
        self.check_flag = True
        self._csr = None

    # ------------------------------------------------------------------ MATLAB methods
    def l_squeeze(self):
        """Remove the empty rows (type ``'matlab_ind'`` -> ``'l_squeezed_matlab_ind'``)."""
        if self.type != "matlab_ind":
            raise ValueError("The matrix must be of type 'matlab_ind ' ")
        self.check()
        temp_mask = np.ravel(self.r_nJump) != 0
        self.r_nJump = _row(np.ravel(self.r_nJump)[temp_mask], np.int32)
        temp_ind = np.arange(1, int(self.l_size) + 1)[temp_mask]
        self.l_ind = _row(temp_ind, np.int32)
        self.l_nJump = np.int32(self.l_ind.shape[1])
        self.type = "l_squeezed_matlab_ind"
        self.l_squeeze_flag = True
        self._csr = None
        self.check()

    def cpp_prepare(self, argMode, nJumpPerBlock_factor=None, blockLengthMax_factor=None):
        """Convert indices to jumps and partition the rows in blocks."""
        from monalisa.sparseMat.m.bmSparseMat_blockPartition import bmSparseMat_blockPartition

        self.check()
        if self.type not in ("matlab_ind", "l_squeezed_matlab_ind"):
            raise ValueError("The matrix must be of type 'matlab_ind ' or  'l_squeezed_matlab_ind ' ")
        if argMode == "one_block":
            l_block_start, block_length, nBlock, zero_block_flag = bmSparseMat_blockPartition(
                self.r_nJump, None, None, "one")
        elif argMode == "multi_block":
            l_block_start, block_length, nBlock, zero_block_flag = bmSparseMat_blockPartition(
                self.r_nJump, nJumpPerBlock_factor, blockLengthMax_factor)
        else:
            raise ValueError("Wrong list of arguments. ")
        if zero_block_flag:
            raise ValueError("The sparse matrix got a zero block. Preparation aborted.")
        self.l_block_start = l_block_start
        self.block_length = block_length
        self.nBlock = nBlock

        n_block = int(np.ravel(nBlock)[0])
        m_block_start = np.zeros((1, n_block), dtype=np.int64)
        r_ind = np.ravel(self.r_ind).astype(np.float64)
        l_ind = None if isempty(self.l_ind) else np.ravel(self.l_ind).astype(np.float64)
        r_jump = (r_ind - np.concatenate([[0.0], r_ind[:-1]])).astype(np.int32)
        squeezed = self.type == "l_squeezed_matlab_ind"
        if squeezed:
            l_jump = (l_ind - np.concatenate([[0.0], l_ind[:-1]])).astype(np.int32)
            self.l_nJump = np.int32(l_jump.size)
        else:
            l_jump = None
            self.l_nJump = np.int32(self.l_size)

        r_nJump = np.ravel(self.r_nJump).astype(np.int64)
        lbs = np.ravel(self.l_block_start).astype(np.int64)
        temp_sum = 0
        current_l_start = 0
        for i in range(n_block):
            last = current_l_start
            current_l_start = int(lbs[i])
            temp_sum += int(r_nJump[last:current_l_start].sum())
            m_block_start[0, i] = temp_sum
            r_jump[temp_sum] = np.int32(r_ind[temp_sum] - 1)
            if squeezed:
                l_jump[current_l_start] = np.int32(l_ind[current_l_start] - 1)
        self.m_block_start = m_block_start
        self.r_jump = _row(r_jump, np.int32)
        self.l_jump = None if l_jump is None else _row(l_jump, np.int32)
        self.r_ind = None
        self.l_ind = None
        self.block_type = argMode
        self.type = "cpp_prepared" if self.type == "matlab_ind" else "l_squeezed_cpp_prepared"
        self._csr = None
        self.check()

    def check(self):
        """Consistency checks of the MATLAB class; raises when one fails."""
        if self.type == "void":
            return
        fail = []
        if self.type not in ("void", "matlab_ind", "l_squeezed_matlab_ind", "cpp_prepared",
                             "l_squeezed_cpp_prepared"):
            fail.append("1")
        r_nJump = None if isempty(self.r_nJump) else np.ravel(self.r_nJump)
        if isempty(self.l_size) or isempty(self.r_size) or isempty(self.l_nJump):
            fail.append("2.1")
        elif r_nJump is None or isempty(self.m_val):
            fail.append("2.2")
        elif int(self.l_size) < 2 or int(self.r_size) < 2 or int(self.l_nJump) < 2:
            fail.append("2.5")
        elif np.sum(r_nJump < 0) > 0:
            fail.append("2.6")
        mySum = None
        if r_nJump is not None:
            mySum = int(np.sum(r_nJump.astype(np.int64)))
            if mySum == 0:
                fail.append("3.1")
            elif mySum != _size2(self.m_val):
                fail.append("3.2")
            if r_nJump.size != int(self.l_nJump):
                fail.append("3.3")
        if self.type in ("matlab_ind", "l_squeezed_matlab_ind"):
            if isempty(self.r_ind) or _size2(self.r_ind) < 2:
                fail.append("4.1")
            elif mySum is not None and mySum != _size2(self.r_ind):
                fail.append("5.1")
        if self.type == "matlab_ind":
            if int(self.l_nJump) != int(self.l_size):
                fail.append("6.1")
            if not isempty(self.r_jump) or not isempty(self.l_jump) or not isempty(self.l_ind):
                fail.append("6.2")
            if self.l_squeeze_flag:
                fail.append("6.3")
        if self.type == "l_squeezed_matlab_ind":
            if isempty(self.l_ind) or _size2(self.l_ind) < 2:
                fail.append("7.1")
            elif int(self.l_nJump) != _size2(self.l_ind):
                fail.append("7.3")
            if not self.l_squeeze_flag:
                fail.append("7.4")
        if self.type in ("cpp_prepared", "l_squeezed_cpp_prepared"):
            if not isempty(self.r_ind) or not isempty(self.l_ind):
                fail.append("8.1")
            if isempty(self.r_jump):
                fail.append("8.2")
        if self.type == "cpp_prepared":
            if not isempty(self.l_jump):
                fail.append("9.1")
            if mySum is not None and mySum != _size2(self.r_jump):
                fail.append("9.2")
            if self.l_squeeze_flag:
                fail.append("9.3")
        if self.type == "l_squeezed_cpp_prepared":
            if isempty(self.l_jump):
                fail.append("10.1")
            elif _size2(self.l_jump) != int(self.l_nJump):
                fail.append("10.2")
            if not self.l_squeeze_flag:
                fail.append("10.3")
        imax = np.iinfo(np.int32).max
        if not (int(self.r_size) < imax and int(self.l_size) < imax):
            fail.append("11.1")
        for f in fail:
            disp(f"Check {f} failed")
        if fail:
            self.check_flag = False
        if not self.check_flag:
            raise ValueError("The sparse matrix did NOT pass the check ! ")

    # ------------------------------------------------------------------ Python helpers
    def csr(self):
        """Decoded structure ``(row_of, row_start, cols, vals)`` of a cpp_prepared matrix:
        stored row ``i`` is output row ``row_of[i]`` with non-zeros
        ``row_start[i]:row_start[i+1]`` in ``cols`` (0-based) / ``vals``."""
        if self._csr is None:
            if self.type not in ("cpp_prepared", "l_squeezed_cpp_prepared"):
                raise ValueError("The bmSparseMat is not cpp_prepared. ")
            r_nJump = np.ravel(self.r_nJump).astype(np.int64)
            row_start = np.concatenate([[0], np.cumsum(r_nJump)])
            cols = _blockwise_cumsum(np.ravel(self.r_jump), np.ravel(self.m_block_start))
            if isempty(self.l_jump):
                row_of = np.arange(int(self.l_nJump), dtype=np.int64)
            else:
                row_of = _blockwise_cumsum(np.ravel(self.l_jump), np.ravel(self.l_block_start))
            vals = np.ascontiguousarray(np.ravel(self.m_val), dtype=np.float32)
            self._csr = (row_of, row_start, cols, vals)
        return self._csr

    def parity_fields(self) -> dict:
        return {f: getattr(self, f) for f in _FIELDS}

    @classmethod
    def from_matlab_fields(cls, fields: dict) -> bmSparseMat:
        """Rebuild an object from the properties recorded in MATLAB."""
        s = cls()
        for f in _FIELDS:
            val = fields.get(f)
            if isinstance(val, np.ndarray) and val.size == 0:
                val = None
            if f in ("l_squeeze_flag", "check_flag") and val is not None:
                val = bool(np.ravel(val)[0])
            setattr(s, f, val)
        return s

    def __repr__(self):
        return (f"bmSparseMat(type={self.type!r}, l_size={self.l_size}, r_size={self.r_size}, "
                f"nnz={_size2(self.m_val)})")


def _blockwise_cumsum(jumps, starts):
    """Absolute positions from jumps whose block-start entries are absolute."""
    jumps = jumps.astype(np.int64)
    out = np.cumsum(jumps)
    starts = np.ravel(starts).astype(np.int64)
    for s in starts[1:]:
        if 0 < s < jumps.size:
            out[s:] -= out[s - 1]
    return out


