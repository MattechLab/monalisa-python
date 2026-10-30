function scenario_tutorial_coilsense(ctx)
% Capture scenario: tutorial 1, coil sensitivity estimation (3D radial
% phyllotaxis, Siemens raw data), plus 3D gridded reconstructions.
% Mirrors demo/script_demo/script_tutorial_1/coilSensitivityEstimation_script.m
% with autoFlag = true (no metadata dialogs) and without display calls.

dataDir = fullfile(ctx.data, 'data_8_tutorial_1');
autoFlag = true;
bodyCoilreader = createRawDataReader(fullfile(dataDir, 'bodyCoil.dat'), autoFlag);
headCoilReader = createRawDataReader(fullfile(dataDir, 'surfaceCoil.dat'), autoFlag);

nShotOff = max(bodyCoilreader.acquisitionParams.nShot_off, ...
               headCoilReader.acquisitionParams.nShot_off);
bodyCoilreader.acquisitionParams.nShot_off = nShotOff;
headCoilReader.acquisitionParams.nShot_off = nShotOff;
bodyCoilreader.acquisitionParams.traj_type = 'full_radial3_phylotaxis';
headCoilReader.acquisitionParams.traj_type = 'full_radial3_phylotaxis';

dK_u = [1, 1, 1] ./ headCoilReader.acquisitionParams.FoV;
N_u = [48, 48, 48];

[y_body, t, ve] = bmCoilSense_nonCart_data(bodyCoilreader, N_u);
y_surface = bmCoilSense_nonCart_data(headCoilReader, N_u);

% 3D gridded reconstructions, one image per channel
x_body = bmMathilda(y_body, t, ve, [], N_u, N_u, dK_u); %#ok<NASGU>
x_surf = bmMathilda(y_surface, t, ve, [], N_u, N_u, dK_u); %#ok<NASGU>

[Gn, Gu, Gut] = bmTraj2SparseMat(t, ve, N_u, dK_u);
mask = bmCoilSense_nonCart_mask_automatic(y_body, Gn, false);
[y_ref, C_ref] = bmCoilSense_nonCart_ref(y_body, Gn, mask, []);
C_array_prime = bmCoilSense_nonCart_primary(y_surface, y_ref, C_ref, Gn, ve, mask);
nIter = 5;
[C, x] = bmCoilSense_nonCart_secondary(y_surface, C_array_prime, y_ref, ...
                                       C_ref, Gn, Gu, Gut, ve, nIter, false); %#ok<ASGLU>

% 3D gridded reconstructions with coil combination, cropping and zero filling
x_comb = bmMathilda(y_surface, t, ve, C, N_u, N_u, dK_u); %#ok<NASGU>
x_crop = bmMathilda(y_surface, t, ve, C(9:40, 9:40, 9:40, :), N_u, [32, 32, 32], dK_u); %#ok<NASGU>
N2 = [64, 64, 64];
C2 = bmImResize(C, N_u, N2);
x_big = bmMathilda(y_surface, t, ve, C2, N2, N2, dK_u); %#ok<NASGU>
ve3 = bmVolumeElement(t, 'voronoi_full_radial3'); %#ok<NASGU>
end
