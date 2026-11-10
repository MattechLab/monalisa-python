"""Monalisa's row-compressed sparse matrix (``SparseMat``) and its products with vectors.
"""

from monalisa.sparse._sparse_mat import SparseMat
from monalisa.sparse._sparse_mat_block_partition import sparse_mat_block_partition
from monalisa.sparse._sparse_mat_complete_matlab_sparse import sparse_mat_complete_matlab_sparse
from monalisa.sparse._sparse_mat_from_matlab_sparse import sparse_mat_from_matlab_sparse
from monalisa.sparse._sparse_mat_r_n_jump_to_index import sparse_mat_r_n_jump_to_index
from monalisa.sparse._sparse_mat_vec import sparse_mat_vec

__all__ = [
    "SparseMat",
    "sparse_mat_block_partition",
    "sparse_mat_complete_matlab_sparse",
    "sparse_mat_from_matlab_sparse",
    "sparse_mat_r_n_jump_to_index",
    "sparse_mat_vec",
]
