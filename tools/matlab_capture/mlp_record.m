function mlp_record(name, inPlain, outs, nIn, nOut)
% mlp_record(name, inPlain, outs, nIn, nOut)
%
% Save one recorded call of function name to
% MLP_STATE.dir/<name>/call_<k>.mat. Records larger than MLP_STATE.maxBytes
% are skipped and only logged.

global MLP_STATE

caller = '';
st = dbstack(2);
if ~isempty(st)
    caller = st(1).name;
end

rec = struct('func', name, ...
             'nargin', nIn, ...
             'nargout', nOut, ...
             'inputs', {inPlain}, ...
             'outputs', {mlp_to_plain(outs)}, ...
             'scenario', MLP_STATE.scenario, ...
             'upstream', MLP_STATE.upstream, ...
             'caller', caller); %#ok<NASGU>
info = whos('rec');

k = MLP_STATE.nrec(name);
status = 'saved';
if info.bytes > MLP_STATE.maxBytes
    status = 'too_large';
else
    d = fullfile(MLP_STATE.dir, name);
    if ~exist(d, 'dir')
        mkdir(d);
    end
    save(fullfile(d, sprintf('call_%03d.mat', k)), 'rec', '-v7');
end
MLP_STATE.log{end+1} = sprintf('%s,%d,%d,%s,%s', name, k, info.bytes, status, caller);
end
