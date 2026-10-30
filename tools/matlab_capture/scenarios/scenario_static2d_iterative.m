function scenario_static2d_iterative(ctx)
% Capture scenario: iterative reconstructions (Sensa, Steva, Sleva) on the 2D
% static demo data, with few iterations. Mirrors static_recon_calls_script.m.
here = pwd;
tmp = tempname; mkdir(tmp); cd(tmp);   % the witness writes its files in the working directory
c = onCleanup(@() cd(here));
for ds = {'data_2_static_radial_simulated_from_cartesian', 'data_3_static_radial_measured'}
    S = load(fullfile(ctx.data, ds{1}, 'data.mat'));
    t = S.t; y = S.y; C = S.C; N_u = S.N_u; dK_u = S.dK_u; frSize = S.frSize;
    ve = bmVolumeElement(t, 'voronoi_full_radial2');
    C_size = size(C); C_size = C_size(1:S.frDim);
    C = bmImResize(C, C_size, frSize);
    [Gn, Gu, Gut] = bmTraj2SparseMat(t, ve, N_u, dK_u);
    x0 = bmNasha(y, Gn, frSize, C, []);
    nIter = 3; nCGD = 4; ve_max = 10*prod(dK_u(:));
    x = bmSensa(x0, y, ve, C, Gu, Gut, frSize, nCGD, ve_max, nIter, bmWitnessInfo('sensa', [1, nIter], false)); %#ok<NASGU>
    x = bmSteva(x0, [], [], y, ve, C, Gu, Gut, frSize, 1, 10, nCGD, ve_max, nIter, bmWitnessInfo('steva', [1, nIter], false)); %#ok<NASGU>
    x = bmSleva(x0, y, ve, C, Gu, Gut, frSize, 2, 'normal', nCGD, ve_max, nIter, bmWitnessInfo('sleva', [1, nIter], false)); %#ok<NASGU>
end
end
