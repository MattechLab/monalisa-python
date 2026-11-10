"""Port of src/optim/bmInitialWitnessInfo.m."""

import numpy as np

from monalisa.optim._witness_info import cell_set


def initial_witness_info(witnessInfo, function_label=None, N_u=None, n_u=None, dK_u=None, ve_max=None,
                         nIter_max=None, nCGD=None, delta=None, rho=None, regul_mode=None):
    """Store the reconstruction parameters in ``witnessInfo.param`` (cells 1-13)."""
    entries = [
        ("function_label", function_label), ("N_u", N_u), ("n_u", n_u), ("dK_u", dK_u),
        ("ve_max", ve_max), ("nIter_max", nIter_max), ("nCGD", nCGD), ("delta", delta), ("rho", rho),
        ("regule_mode", regul_mode),
        ("objective_function", np.zeros((1, int(nIter_max)))),
        ("data_fidelity_term", np.zeros((1, int(nIter_max)))),
        ("regule_term", np.zeros((1, int(nIter_max)))),
    ]
    for k, (name, value) in enumerate(entries, start=1):
        cell_set(witnessInfo.param_name, k, name)
        cell_set(witnessInfo.param, k, value)
