function run_capture(scenario, outRoot, upstreamRoot, varargin)
% run_capture(scenario, outRoot, upstreamRoot, ...)
%
% Instrument the upstream Monalisa sources, run the capture scenario
% scenario_<scenario>.m and write the recorded calls to outRoot/<scenario>.
%
% Name-value options: 'maxPerFunc' (6), 'firstK' (2), 'maxBytes' (64e6),
% 'reinstrument' (true).

opt = struct('maxPerFunc', 6, 'firstK', 2, 'maxBytes', 64e6, 'reinstrument', true);
for i = 1:2:numel(varargin)
    opt.(varargin{i}) = varargin{i+1};
end

here = fileparts(mfilename('fullpath'));
instrDir = fullfile(here, '..', '..', 'build', 'matlab_instrumented', 'src');
if opt.reinstrument || ~exist(instrDir, 'dir')
    n = mlp_instrument(fullfile(upstreamRoot, 'src'), instrDir);
    fprintf('Instrumented %d functions in %s\n', n, instrDir);
end

restoredefaultpath;
addpath(here);
addpath(fullfile(here, 'scenarios'));
addpath(genpath(instrDir));
addpath(genpath(fullfile(upstreamRoot, 'third_part')));
addpath(genpath(fullfile(upstreamRoot, 'demo', 'function_demo')));

[~, commit] = system(sprintf('git -C "%s" rev-parse HEAD', upstreamRoot));

outDir = fullfile(outRoot, scenario);
if exist(outDir, 'dir')
    rmdir(outDir, 's');
end
mkdir(outDir);

global MLP_STATE
MLP_STATE = struct('enabled', true, ...
                   'dir', outDir, ...
                   'scenario', scenario, ...
                   'upstream', strtrim(commit), ...
                   'maxPerFunc', opt.maxPerFunc, ...
                   'firstK', opt.firstK, ...
                   'maxSeen', 20000, ...
                   'maxBytes', opt.maxBytes, ...
                   'seen', containers.Map(), ...
                   'nrec', containers.Map(), ...
                   'sigs', containers.Map(), ...
                   'log', {{}});

ctx = struct('upstream', upstreamRoot, ...
             'data', fullfile(upstreamRoot, 'demo', 'data_demo'));
set(0, 'DefaultFigureVisible', 'off');
rng(0);
tStart = tic;
scenarioError = [];
try
    feval(['scenario_', scenario], ctx);
catch scenarioError
end
MLP_STATE.enabled = false;

fid = fopen(fullfile(outDir, 'capture_log.csv'), 'w');
fprintf(fid, 'func,call,bytes,status,caller\n');
fprintf(fid, '%s\n', MLP_STATE.log{:});
fclose(fid);

fns = keys(MLP_STATE.seen);
fid = fopen(fullfile(outDir, 'call_counts.csv'), 'w');
fprintf(fid, 'func,n_calls,n_recorded\n');
for i = 1:numel(fns)
    fprintf(fid, '%s,%d,%d\n', fns{i}, MLP_STATE.seen(fns{i}), MLP_STATE.nrec(fns{i}));
end
fclose(fid);
fprintf('Scenario %s done in %.1f s: %d functions called.\n', scenario, toc(tStart), numel(fns));
if ~isempty(scenarioError)
    rethrow(scenarioError);
end
end
