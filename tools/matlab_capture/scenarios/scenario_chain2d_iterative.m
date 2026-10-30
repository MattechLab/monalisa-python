function scenario_chain2d_iterative(ctx)
% Capture scenario: chain reconstructions (TevaMorphosia_chain) on the 2D
% chain demo data 5, without and with deformation fields, few iterations.
% Mirrors chain_recon_calls_script.m.
here = pwd;
tmp = tempname; mkdir(tmp); cd(tmp);
c = onCleanup(@() cd(here));
S = load(fullfile(ctx.data, 'data_5_chain_radial_simulated_from_cartesian', 'data.mat'));
t = S.t; y = S.y; C = S.C; N_u = S.N_u; dK_u = S.dK_u; frSize = S.frSize; nFr = 6;
t = t(1:nFr); y = y(1:nFr);
ve = bmVolumeElement(t, 'voronoi_full_radial2');
C_size = size(C); C_size = C_size(1:S.frDim);
C = bmImResize(C, C_size, frSize);
x0 = cell(nFr, 1);
for i = 1:nFr
    x0{i} = bmMathilda(y{i}, t{i}, ve{i}, C, N_u, frSize, dK_u, [], [], [], []);
end
[Gu, Gut] = bmTraj2SparseMat(t, ve, N_u, dK_u);
nIter = 3; nCGD = 4; ve_max = 10*prod(dK_u(:));
x = bmTevaMorphosia_chain(x0, [], [], y, ve, C, Gu, Gut, frSize, [], [], 0.1, 1, 'normal', ...
                          nCGD, ve_max, nIter, bmWitnessInfo('teva', [1, nIter], false));
[DF_to_prev, ~] = bmImDeformFieldChain_imRegDemons23(x, frSize, 'curr_to_prev', 50, 1, [], S.reg_mask, 10);
[Tu1, Tu1t] = bmImDeformField2SparseMat(DF_to_prev, N_u, [], true);
x = bmTevaMorphosia_chain(x0, [], [], y, ve, C, Gu, Gut, frSize, Tu1, Tu1t, 0.3, 3, 'normal', ...
                          nCGD, ve_max, nIter, bmWitnessInfo('teva_df', [1, nIter], false)); %#ok<NASGU>
end
