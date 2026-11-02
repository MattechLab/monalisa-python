function registration_reference(out_dir, monalisa_dir)
% End-to-end reference of the registration-based (motion-compensated)
% reconstructions, with the parameters of demo/script_demo/script_recon_calls:
%   chain (demo data 5): Mathilda -> TevaMorphosia_chain -> demons fields
%   (bmImDeformFieldChain_imRegDemons23, 500 iterations) -> TevaMorphosia,
%   TevaDuoMorphosia and SensitivaMorphosia chains with deformation matrices;
%   sheet (demo data 7): demons fields of the Mathilda reconstructions
%   (bmImDeformFieldSheet_imRegDemons23).
% Every stage is saved, so that the Python port can be validated stage by
% stage (solvers with the MATLAB fields) and as a whole (with its own fields).

addpath(genpath(fullfile(monalisa_dir, 'src')));
if ~exist(out_dir, 'dir'), mkdir(out_dir); end
here = pwd; tmp = tempname; mkdir(tmp); cd(tmp); c = onCleanup(@() cd(here));
data_dir = fullfile(monalisa_dir, 'demo', 'data_demo');

% ---------------------------------------------------------------- chain
S = load(fullfile(data_dir, 'data_5_chain_radial_simulated_from_cartesian', 'data.mat'));
t = S.t; y = S.y; N_u = S.N_u; dK_u = S.dK_u; frSize = S.frSize; nFr = S.nFr; reg_mask = S.reg_mask;
ve = bmVolumeElement(t, 'voronoi_full_radial2');
C_size = size(S.C); C_size = C_size(1:S.frDim);
C = bmImResize(S.C, C_size, frSize);
x0 = cell(nFr, 1);
for i = 1:nFr
    x0{i} = bmMathilda(y{i}, t{i}, ve{i}, C, N_u, frSize, dK_u, [], [], [], []);
end
[~, Gu, Gut] = bmTraj2SparseMat(t, ve, N_u, dK_u);
ve_max = 10*prod(dK_u(:)); nCGD = 4; nIter = 30;
noWitness = @(name) bmWitnessInfo(name, [], false);

tic;
x1 = bmTevaMorphosia_chain(x0, [], [], y, ve, C, Gu, Gut, frSize, [], [], 0.1, 1, 'normal', ...
                           nCGD, ve_max, nIter, noWitness('teva'));
time_teva = toc;

tic;
[DF_to_prev, imReg_to_prev] = bmImDeformFieldChain_imRegDemons23(x1, frSize, 'curr_to_prev', 500, 1, [], reg_mask, 10);
time_demons = toc;
[DF_to_next, imReg_to_next] = bmImDeformFieldChain_imRegDemons23(x1, frSize, 'curr_to_next', 500, 1, [], reg_mask, 10);
[Tu1, Tu1t] = bmImDeformField2SparseMat(DF_to_prev, N_u, [], true);
[Tu2, Tu2t] = bmImDeformField2SparseMat(DF_to_next, N_u, [], true);

x_teva_DF = bmTevaMorphosia_chain(x0, [], [], y, ve, C, Gu, Gut, frSize, Tu1, Tu1t, 0.3, 3, 'normal', ...
                                  nCGD, ve_max, nIter, noWitness('teva_df'));
x_duo_DF = bmTevaDuoMorphosia_chain(x0, [], [], [], [], y, ve, C, Gu, Gut, frSize, Tu1, Tu1t, Tu2, Tu2t, ...
                                    0.3, 3, 'normal', nCGD, ve_max, nIter, noWitness('duo_df'));
x_sens_DF = bmSensitivaMorphosia_chain(x0, y, ve, C, Gu, Gut, frSize, Tu1, Tu1t, 3, 'normal', ...
                                       nCGD, ve_max, nIter, noWitness('sens_df'));

save(fullfile(out_dir, 'chain_data5.mat'), 'x0', 'x1', 'DF_to_prev', 'imReg_to_prev', ...
     'DF_to_next', 'imReg_to_next', 'x_teva_DF', 'x_duo_DF', 'x_sens_DF', 'time_teva', 'time_demons', '-v7.3');

% ---------------------------------------------------------------- sheet
S = load(fullfile(data_dir, 'data_7_sheet_radial_simulated_from_XCAT', 'data.mat'));
nCell = [6, 4];  % sub-sheet, to keep the reference small
t = S.t(1:nCell(1), 1:nCell(2)); y = S.y(1:nCell(1), 1:nCell(2));
ve = bmVolumeElement(t, 'voronoi_full_radial2');
C_size = size(S.C); C_size = C_size(1:S.frDim);
C = bmImResize(S.C, C_size, S.frSize);
xs0 = cell(nCell);
for i = 1:numel(xs0)
    xs0{i} = bmMathilda(y{i}, t{i}, ve{i}, C, S.N_u, S.frSize, S.dK_u, [], [], [], []);
end
[DF_sheet_1, DF_sheet_2, imReg_sheet_1, imReg_sheet_2] = ...
    bmImDeformFieldSheet_imRegDemons23(xs0, S.frSize, 'curr_to_prev', [100, 100], 1, [], S.reg_mask, 10);
save(fullfile(out_dir, 'sheet_data7.mat'), 'xs0', 'DF_sheet_1', 'DF_sheet_2', 'imReg_sheet_1', ...
     'imReg_sheet_2', '-v7.3');
end
