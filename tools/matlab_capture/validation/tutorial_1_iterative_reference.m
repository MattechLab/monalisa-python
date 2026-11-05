function tutorial_1_iterative_reference(e2eDir, monalisaRoot)
% tutorial_1_iterative_reference(e2eDir, monalisaRoot)
%
% Iterative reconstructions of tutorial 1 (reconstructions_script.m, sections
% "Iterative Sense reconstruction: Sensa" and "Compressed Sensing
% reconstruction"), from the MATLAB outputs of scenario_tutorial_recon in
% e2eDir (mitosius_sequential, coil_sensitivity_map.mat, reconstructions.mat,
% binning.mat). Same parameters as the tutorial, without display. Gu/Gut are
% built for the nFr bins used only (each bin is independent, so the result is
% the same as building them for all bins). Saves e2eDir/iterative.mat with
% x_sensa and x_cs (cells nFr x 1).
%
%   matlab -batch "addpath('tools/matlab_capture/validation'); \
%       tutorial_1_iterative_reference('fixtures/matlab_e2e/tutorial_1', '/path/to/monalisa')"

restoredefaultpath;
addpath(genpath(fullfile(monalisaRoot, 'src')));
addpath(genpath(fullfile(monalisaRoot, 'third_part')));
e2eDir = char(java.io.File(e2eDir).getCanonicalPath());

B = load(fullfile(e2eDir, 'binning.mat'), 'p');
FoV = B.p.FoV;
matrix_size = FoV / 3;
N_u = [matrix_size, matrix_size, matrix_size];
n_u = N_u;
dK_u = [1, 1, 1] / FoV;
S = load(fullfile(e2eDir, 'coil_sensitivity_map.mat'), 'C');
C = bmImResize(S.C, [48, 48, 48], N_u);
R = load(fullfile(e2eDir, 'reconstructions.mat'), 'x1');
x1 = R.x1;
nFr = numel(x1);

mDir = fullfile(e2eDir, 'mitosius_sequential');
y = bmMitosius_load(mDir, 'y'); t = bmMitosius_load(mDir, 't'); ve = bmMitosius_load(mDir, 've');
y = y(1:nFr); t = t(1:nFr); ve = ve(1:nFr);

% witness files are written to the working directory
witnessDir = tempname; mkdir(witnessDir); oldDir = cd(witnessDir);
cleanup = onCleanup(@() cd(oldDir));

%% Iterative Sense reconstruction: Sensa
[Gu, Gut] = bmTraj2SparseMat(t, ve, N_u, dK_u);
nCGD = 4;
x_sensa = cell(nFr, 1);
tic
for i = 1:nFr
    nIter       = 30;
    witness_ind = 1:3:nIter;
    witnessInfo = bmWitnessInfo(['sensa_frame_', num2str(i)], witness_ind);
    ve_max  = 10*prod(dK_u(:));
    x_sensa{i} = bmSensa(x1{i}, y{i}, ve{i}, C, Gu{i}, Gut{i}, n_u, nCGD, ve_max, nIter, witnessInfo);
end
fprintf('Sensa: %.0f s\n', toc);

%% Compressed Sensing reconstruction
[Gu, Gut] = bmTraj2SparseMat(t, ve, N_u, dK_u);
nIter = 30;
delta     = 0.1;
rho       = 10*delta;
witness_ind = 1:3:nIter;
nCGD    = 4;
tic
x_cs = bmTevaMorphosia_chain(x1, [], [], y(1:nFr), ve(1:nFr), C, Gu, Gut, n_u, [], [], ...
                             delta, rho, 'normal', nCGD, ve_max, nIter, ...
                             bmWitnessInfo('tevaMorphosia_d0p1_r1_nCGD4', witness_ind));
fprintf('TevaMorphosia: %.0f s\n', toc);

save(fullfile(e2eDir, 'iterative.mat'), 'x_sensa', 'x_cs', '-v7.3');
end
