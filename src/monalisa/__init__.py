"""Monalisa: reconstruction of non-Cartesian and Cartesian MRI data.

Python port of the MATLAB toolbox Monalisa (MattechLab, https://github.com/MattechLab/monalisa).

=============================  ==================================================================
``monalisa.recon``             reconstructions: gridded, iterative, chain (motion-compensated)
``monalisa.io``                raw data readers, acquisition parameters, MATLAB v7.3 files
``monalisa.trajectory``        trajectories, grid size and step, line format
``monalisa.geometry``          volume elements (density compensation), Voronoi cells
``monalisa.gridding``          gridding, sparse gridding and deformation matrices
``monalisa.sparse``            Monalisa's sparse matrix and its products
``monalisa.fourier``           centered DFTs, deapodization, non-Cartesian Fourier model
``monalisa.coil``              coil sensitivity estimation and coil combination
``monalisa.binning``           binning of the lines, binned data on disk (mitosius)
``monalisa.image``             crop, zero fill, resize, deformation, smoothing, RMS and MIP
``monalisa.registration``      demons deformation fields between frames
``monalisa.optim``             building blocks of the iterative reconstructions
``monalisa.display``           image viewers and polygon masks
``monalisa.array``             array formats (block, column, point) and cells
``monalisa.util``              argument defaults, clock
=============================  ==================================================================

Every public function and class is also available from the top-level package::

    import monalisa as ml
    x = ml.mathilda(y, t, ve, C, N_u, n_u, dK_u)

The functions keep the arguments, array shapes (column-major) and precision of the MATLAB
functions they are ported from. docs/renaming.md lists the MATLAB name of each one;
``find_function("bmMathilda")`` returns the Python function of a MATLAB name.
"""

from __future__ import annotations

import importlib

from monalisa import (
    array,
    binning,
    coil,
    display,
    fourier,
    geometry,
    gridding,
    image,
    io,
    optim,
    recon,
    registration,
    sparse,
    trajectory,
    util,
)
from monalisa._upstream import MATLAB_NAMES, UPSTREAM_COMMIT
from monalisa.array import (
    block_reshape,
    cell_to_array,
    col,
    col_reshape,
    index_to_multi_index,
    is_block_shape,
    is_col_shape,
    is_scalar,
    permute_to_col,
    permute_to_point,
    point_reshape,
    to_single,
    zero,
)
from monalisa.binning import mitosis, mitosius_create, mitosius_load
from monalisa.coil import (
    coil_sense_non_cart_data,
    coil_sense_non_cart_mask_automatic,
    coil_sense_non_cart_primary,
    coil_sense_non_cart_ref,
    coil_sense_non_cart_secondary,
    coil_sense_pinv,
    detect_roi,
    select_roi,
    threshold_rms_mip,
)
from monalisa.display import poly2mask, roipoly, show_image
from monalisa.fourier import (
    deapodization,
    dft1,
    dft1_conj_trans,
    dft2,
    dft2_conj_trans,
    dft3,
    dft3_conj_trans,
    fc,
    fc_conj,
    idf,
    idf1,
    idf1_conj_trans,
    idf2,
    idf2_conj_trans,
    idf3,
    idf3_conj_trans,
    kf,
    kf_conj,
    nakatsha,
    nakatsha_matlab,
    shanna,
    shanna_matlab,
)
from monalisa.geometry import (
    volume_element,
    volume_element1,
    volume_element_cartesian2,
    volume_element_center_out_radial3,
    volume_element_full_radial3,
    volume_element_random_partial_cartesian2_x,
    volume_element_random_partial_cartesian3_x,
    volume_element_voronoi_box2,
    volume_element_voronoi_center_out_radial2,
    volume_element_voronoi_full_radial2,
    volume_element_voronoi_full_radial3,
    voronoi,
)
from monalisa.gridding import (
    gridder_n2u_leight,
    im_deform_field_to_sparse_mat,
    im_deform_field_to_sparse_mat_ind_weight,
    traj_to_sparse_mat,
)
from monalisa.image import (
    im_crop,
    im_deform,
    im_deform_field_hard_thresholding2,
    im_deform_t,
    im_dim,
    im_laplace_equation_solver,
    im_laplace_iterator,
    im_laplacian,
    im_pseudo_diffusion,
    im_pseudo_diffusion_in_mask,
    im_reshape,
    im_resize,
    im_zero_fill,
    mip,
    rms,
)
from monalisa.io import (
    IsmrmrdReader,
    MriAcquisitionParam,
    RawDataReader,
    SiemensReader,
    check_dir,
    check_metadata_interactive,
    correct_metadata_interactive,
    create_dir,
    create_raw_data_reader,
    ismrmrd_read_meta_data,
    ismrmrd_read_raw_data,
    loadmat73,
    savemat73,
    siemens_read_meta_data,
    siemens_read_raw_data,
)
from monalisa.optim import (
    WitnessInfo,
    axpy,
    back_gradient,
    back_gradient_n,
    back_gradient_n_t,
    back_gradient_t,
    euclidean_prod,
    initial_witness_info,
    minus,
    mult,
    plus,
    prox_one_norm,
    squared_norm,
    y_norm,
    y_ve_reshape,
)
from monalisa.recon import (
    mathilda,
    nasha,
    sensa,
    sensitiva_morphosia_chain,
    sleva,
    steva,
    teva_duo_morphosia_chain,
    teva_morphosia_chain,
)
from monalisa.registration import im_deform_field_chain_im_reg_demons23, im_deform_field_sheet_im_reg_demons23
from monalisa.sparse import (
    SparseMat,
    sparse_mat_block_partition,
    sparse_mat_complete_matlab_sparse,
    sparse_mat_from_matlab_sparse,
    sparse_mat_r_n_jump_to_index,
    sparse_mat_vec,
)
from monalisa.trajectory import (
    low_res,
    phyllotaxis_angle3,
    traj,
    traj_format,
    traj_full_radial3_phyllotaxis_line_assym2,
    traj_grid,
    traj_grid_size,
    traj_grid_step,
    traj_line_direction,
    traj_line_reshape,
    traj_n_line,
    traj_norm,
    traj_squared_norm,
)
from monalisa.util import default_grid, default_kernel, default_sparse_type, time_in_second, varargin

__version__ = "0.1.2"


def find_function(matlab_name: str):
    """The Python function or class ported from the MATLAB function ``matlab_name``.

    Returns ``None`` when it is not ported. Example: ``find_function("bmMathilda")`` is
    ``monalisa.recon.mathilda``.
    """
    target = MATLAB_NAMES.get(matlab_name)
    if target is None:
        return None
    package, name = target.split(".")
    return getattr(importlib.import_module(f"monalisa.{package}"), name)


__all__ = [
    "MATLAB_NAMES",
    "UPSTREAM_COMMIT",
    "find_function",
    "array",
    "binning",
    "coil",
    "display",
    "fourier",
    "geometry",
    "gridding",
    "image",
    "io",
    "optim",
    "recon",
    "registration",
    "sparse",
    "trajectory",
    "util",
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
    "mitosis",
    "mitosius_create",
    "mitosius_load",
    "coil_sense_non_cart_data",
    "coil_sense_non_cart_mask_automatic",
    "coil_sense_non_cart_primary",
    "coil_sense_non_cart_ref",
    "coil_sense_non_cart_secondary",
    "coil_sense_pinv",
    "detect_roi",
    "select_roi",
    "threshold_rms_mip",
    "poly2mask",
    "roipoly",
    "show_image",
    "deapodization",
    "dft1",
    "dft1_conj_trans",
    "dft2",
    "dft2_conj_trans",
    "dft3",
    "dft3_conj_trans",
    "fc",
    "fc_conj",
    "idf",
    "idf1",
    "idf1_conj_trans",
    "idf2",
    "idf2_conj_trans",
    "idf3",
    "idf3_conj_trans",
    "kf",
    "kf_conj",
    "nakatsha",
    "nakatsha_matlab",
    "shanna",
    "shanna_matlab",
    "volume_element",
    "volume_element1",
    "volume_element_cartesian2",
    "volume_element_center_out_radial3",
    "volume_element_full_radial3",
    "volume_element_random_partial_cartesian2_x",
    "volume_element_random_partial_cartesian3_x",
    "volume_element_voronoi_box2",
    "volume_element_voronoi_center_out_radial2",
    "volume_element_voronoi_full_radial2",
    "volume_element_voronoi_full_radial3",
    "voronoi",
    "gridder_n2u_leight",
    "im_deform_field_to_sparse_mat",
    "im_deform_field_to_sparse_mat_ind_weight",
    "traj_to_sparse_mat",
    "im_crop",
    "im_deform",
    "im_deform_field_hard_thresholding2",
    "im_deform_t",
    "im_dim",
    "im_laplace_equation_solver",
    "im_laplace_iterator",
    "im_laplacian",
    "im_pseudo_diffusion",
    "im_pseudo_diffusion_in_mask",
    "im_reshape",
    "im_resize",
    "im_zero_fill",
    "mip",
    "rms",
    "IsmrmrdReader",
    "MriAcquisitionParam",
    "RawDataReader",
    "SiemensReader",
    "check_dir",
    "check_metadata_interactive",
    "correct_metadata_interactive",
    "create_dir",
    "create_raw_data_reader",
    "ismrmrd_read_meta_data",
    "ismrmrd_read_raw_data",
    "loadmat73",
    "savemat73",
    "siemens_read_meta_data",
    "siemens_read_raw_data",
    "WitnessInfo",
    "axpy",
    "back_gradient",
    "back_gradient_n",
    "back_gradient_n_t",
    "back_gradient_t",
    "euclidean_prod",
    "initial_witness_info",
    "minus",
    "mult",
    "plus",
    "prox_one_norm",
    "squared_norm",
    "y_norm",
    "y_ve_reshape",
    "mathilda",
    "nasha",
    "sensa",
    "sensitiva_morphosia_chain",
    "sleva",
    "steva",
    "teva_duo_morphosia_chain",
    "teva_morphosia_chain",
    "im_deform_field_chain_im_reg_demons23",
    "im_deform_field_sheet_im_reg_demons23",
    "SparseMat",
    "sparse_mat_block_partition",
    "sparse_mat_complete_matlab_sparse",
    "sparse_mat_from_matlab_sparse",
    "sparse_mat_r_n_jump_to_index",
    "sparse_mat_vec",
    "low_res",
    "phyllotaxis_angle3",
    "traj",
    "traj_format",
    "traj_full_radial3_phyllotaxis_line_assym2",
    "traj_grid",
    "traj_grid_size",
    "traj_grid_step",
    "traj_line_direction",
    "traj_line_reshape",
    "traj_n_line",
    "traj_norm",
    "traj_squared_norm",
    "default_grid",
    "default_kernel",
    "default_sparse_type",
    "time_in_second",
    "varargin",
]
