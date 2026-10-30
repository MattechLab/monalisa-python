function scenario_static2d(ctx)
% Capture scenario: 2D static radial demo data, gridded reconstruction.
% Mirrors demo/script_demo/script_recon_calls/static_recon_calls_script.m
% without display calls.

datasets = {'data_1_static_radial_simulated_from_XCAT', ...
            'data_2_static_radial_simulated_from_cartesian', ...
            'data_3_static_radial_measured'};

for k = 1:numel(datasets)
    S = load(fullfile(ctx.data, datasets{k}, 'data.mat'));
    t = S.t;
    y = S.y;
    C = S.C;
    N_u = S.N_u;
    dK_u = S.dK_u;
    frSize = S.frSize;
    frDim = S.frDim;

    ve = bmVolumeElement(t, 'voronoi_full_radial2');

    C_size = size(C);
    C_size = C_size(1:frDim);
    C = bmImResize(C, C_size, frSize);

    x0 = bmMathilda(y, t, ve, C, N_u, frSize, dK_u, [], [], [], []); %#ok<NASGU>
    x0 = bmMathilda(y, t, ve, [], N_u, N_u, dK_u); %#ok<NASGU>
    x0 = bmMathilda(y, t, ve); %#ok<NASGU>
    x0 = bmMathilda(y, t, ve, C, N_u, frSize, dK_u, 'kaiser', [], []); %#ok<NASGU>
end
end
