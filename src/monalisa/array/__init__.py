"""Array formats of Monalisa: block ``[N_u, nCh]``, column ``[prod(N_u), nCh]`` and point
``[nCh, nPt]`` formats of images and data, and cells of arrays.
"""

from monalisa.array._block_reshape import block_reshape
from monalisa.array._cell_to_array import cell_to_array
from monalisa.array._col import col
from monalisa.array._col_reshape import col_reshape
from monalisa.array._index_to_multi_index import index_to_multi_index
from monalisa.array._is_block_shape import is_block_shape
from monalisa.array._is_col_shape import is_col_shape
from monalisa.array._is_scalar import is_scalar
from monalisa.array._permute_to_col import permute_to_col
from monalisa.array._permute_to_point import permute_to_point
from monalisa.array._point_reshape import point_reshape
from monalisa.array._to_single import to_single
from monalisa.array._zero import zero

__all__ = [
    "block_reshape",
    "cell_to_array",
    "col",
    "col_reshape",
    "index_to_multi_index",
    "is_block_shape",
    "is_col_shape",
    "is_scalar",
    "permute_to_col",
    "permute_to_point",
    "point_reshape",
    "to_single",
    "zero",
]
