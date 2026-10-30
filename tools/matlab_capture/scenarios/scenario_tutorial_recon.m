function scenario_tutorial_recon(ctx)
% Capture scenario: tutorial 1 binning, mitosius and gridded reconstructions
% on the full brain scan. Mirrors binnings_script.m, mitosius_script.m and the
% bmMathilda part of reconstructions_script.m without display, with
% autoFlag = true and with the interactive ROI (roipoly) replaced by the
% fixed rule used by examples/tutorial_1 in Python. Stage outputs are saved
% to fixtures/matlab_e2e/tutorial_1 for the end-to-end comparison.

here = fileparts(mfilename('fullpath'));
e2eDir = fullfile(here, '..', '..', '..', 'fixtures', 'matlab_e2e', 'tutorial_1');
if ~exist(e2eDir, 'dir'), mkdir(e2eDir); end
dataDir = fullfile(ctx.data, 'data_8_tutorial_1');
coilDir = fullfile(here, '..', '..', '..', 'fixtures', 'matlab_e2e', 'tutorial_1');

% --- coil sensitivity (as in scenario_tutorial_coilsense) -------------------
autoFlag = true;
bodyCoilreader = createRawDataReader(fullfile(dataDir, 'bodyCoil.dat'), autoFlag);
headCoilReader = createRawDataReader(fullfile(dataDir, 'surfaceCoil.dat'), autoFlag);
nShotOff = max(bodyCoilreader.acquisitionParams.nShot_off, headCoilReader.acquisitionParams.nShot_off);
bodyCoilreader.acquisitionParams.nShot_off = nShotOff;
headCoilReader.acquisitionParams.nShot_off = nShotOff;
bodyCoilreader.acquisitionParams.traj_type = 'full_radial3_phylotaxis';
headCoilReader.acquisitionParams.traj_type = 'full_radial3_phylotaxis';
dK_u = [1, 1, 1] ./ headCoilReader.acquisitionParams.FoV;
N_u = [48, 48, 48];
[y_body, t, ve] = bmCoilSense_nonCart_data(bodyCoilreader, N_u);
y_surface = bmCoilSense_nonCart_data(headCoilReader, N_u);
[Gn, Gu, Gut] = bmTraj2SparseMat(t, ve, N_u, dK_u);
mask = bmCoilSense_nonCart_mask_automatic(y_body, Gn, autoFlag);
[y_ref, C_ref] = bmCoilSense_nonCart_ref(y_body, Gn, mask, []);
C_array_prime = bmCoilSense_nonCart_primary(y_surface, y_ref, C_ref, Gn, ve, mask);
C = bmCoilSense_nonCart_secondary(y_surface, C_array_prime, y_ref, C_ref, Gn, Gu, Gut, ve, 5, false);
save(fullfile(coilDir, 'coil_sensitivity_map.mat'), 'C');
clear y_body y_surface t ve Gn Gu Gut y_ref C_ref C_array_prime

% --- binnings ---------------------------------------------------------------
reader = createRawDataReader(fullfile(dataDir, 'brainScan.dat'), autoFlag);
p = reader.acquisitionParams;
nSeg = p.nSeg;
nExcludeMeasures = p.nShot_off * nSeg;
nLines = p.nLine;
timeStamp = double(p.timestamp);
timestampMs = (timeStamp - min(timeStamp)) * 2.5;
mask = true(1, nLines);
mask(1, 1:nExcludeMeasures) = false;
for K = 0:floor(nLines / nSeg)
    idx = 1 + K * nSeg;
    if idx <= nLines
        mask(idx) = false;
    end
end
allLinesMask = mask;
temporalWindowMs = 5 * 1000;
startTime = timestampMs(nExcludeMeasures + 1);
nMasks = floor((timestampMs(end) - startTime) / temporalWindowMs);
mask = false(nMasks, nLines);
for i = 1:nMasks
    windowStart = startTime + (i - 1) * temporalWindowMs;
    singlemask = (timestampMs >= windowStart) & (timestampMs < windowStart + temporalWindowMs);
    for K = 0:floor(nLines / nSeg)
        idx = 1 + K * nSeg;
        if idx <= nLines
            singlemask(idx) = false;
        end
    end
    mask(i, :) = singlemask;
end
sequentialMask = mask;
save(fullfile(e2eDir, 'binning.mat'), 'allLinesMask', 'sequentialMask', 'p');

% --- mitosius ---------------------------------------------------------------
p.traj_type = 'full_radial3_phylotaxis';
y_tot = reader.readRawData(true, true);
t_tot = bmTraj(p);
ve_tot = bmVolumeElement(t_tot, 'voronoi_full_radial3');
FoV = p.FoV;
matrix_size = FoV / 3;
N_u = [matrix_size, matrix_size, matrix_size];
C = bmImResize(C, [48, 48, 48], N_u);
x_tot = bmMathilda(y_tot, t_tot, ve_tot, C, N_u, N_u, [1, 1, 1] / 384);
% fixed replacement of getimage/roipoly: central slice, centered disk of radius N/4
temp_im = abs(x_tot(:, :, N_u(3)/2 + 1));
[gx, gy] = ndgrid(1:N_u(1), 1:N_u(2));
temp_roi = (gx - (N_u(1)/2 + 1)).^2 + (gy - (N_u(2)/2 + 1)).^2 <= (N_u(1)/4)^2;
normalize_val = mean(temp_im(temp_roi(:)));
y_tot = y_tot / normalize_val;
save(fullfile(e2eDir, 'mitosius_prep.mat'), 'x_tot', 'normalize_val', 've_tot', '-v7.3');
for b = {'allLines', 'sequential'}
    if strcmp(b{1}, 'allLines'), mask = allLinesMask; else, mask = sequentialMask; end
    mask = reshape(mask, [size(mask, 1), p.nSeg, size(mask, 2) / p.nSeg]);
    mask(:, 1, :) = [];
    mask(:, :, 1:p.nShot_off) = [];
    mask = bmPointReshape(mask);
    [y, t] = bmMitosis(y_tot, t_tot, mask);
    y = bmPermuteToCol(y);
    ve = bmVolumeElement(t, 'voronoi_full_radial3');
    bmMitosius_create(fullfile(e2eDir, ['mitosius_', b{1}]), y, t, ve);
end
clear y_tot t_tot ve_tot y t ve

% --- reconstructions (gridded) ----------------------------------------------
n_u = N_u;
dK_u = [1, 1, 1] / FoV;
mDir = fullfile(e2eDir, 'mitosius_allLines');
y = bmMitosius_load(mDir, 'y'); t = bmMitosius_load(mDir, 't'); ve = bmMitosius_load(mDir, 've');
x0 = bmMathilda(y{1}, t{1}, ve{1}, C, N_u, n_u, dK_u, [], [], [], []);
mDir = fullfile(e2eDir, 'mitosius_sequential');
y = bmMitosius_load(mDir, 'y'); t = bmMitosius_load(mDir, 't'); ve = bmMitosius_load(mDir, 've');
nFr = 8;
x1 = cell(nFr, 1);
for i = 1:nFr
    x1{i} = bmMathilda(y{i}, t{i}, ve{i}, C, N_u, n_u, dK_u, [], [], [], []);
end
save(fullfile(e2eDir, 'reconstructions.mat'), 'x0', 'x1', '-v7.3');
end
