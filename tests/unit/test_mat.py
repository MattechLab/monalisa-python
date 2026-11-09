"""MATLAB semantics helpers (monalisa._mat): column order and mixed-precision arithmetic."""

import numpy as np

from monalisa._mat import mixed, repmat


def test_mixed_scalar_broadcast_and_double_operand():
    a = np.arange(6, dtype=np.float32).reshape(2, 3, order="F")
    assert mixed(np.multiply, np.float32(0.1), a).dtype == np.float32
    x = mixed(np.multiply, 0.1, a)  # a Python float is a MATLAB double: computed in double
    np.testing.assert_array_equal(x, (0.1 * a.astype(np.float64)).astype(np.float32))
    assert x.flags.f_contiguous


def test_repmat_is_column_order_tile():
    x = np.arange(6.0).reshape(3, 2, order="F")
    r = repmat(x, 2, 3)
    np.testing.assert_array_equal(r, np.tile(x, (2, 3)))
    assert r.flags.f_contiguous
    np.testing.assert_array_equal(repmat(np.arange(3.0)[:, None], [1, 4]), np.tile(np.arange(3.0)[:, None], (1, 4)))
