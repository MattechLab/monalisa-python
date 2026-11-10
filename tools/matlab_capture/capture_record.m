function capture_record(name, inPlain, outs, nIn, nOut)
% capture_record(name, inPlain, outs, nIn, nOut)
%
% Save one recorded call of function name to
% CAPTURE_STATE.dir/<name>/call_<k>.mat. Records larger than CAPTURE_STATE.maxBytes
% are skipped and only logged.

global CAPTURE_STATE

caller = '';
st = dbstack(2);
if ~isempty(st)
    caller = st(1).name;
end

rec = struct('func', name, ...
             'nargin', nIn, ...
             'nargout', nOut, ...
             'inputs', {inPlain}, ...
             'outputs', {capture_to_plain(outs)}, ...
             'scenario', CAPTURE_STATE.scenario, ...
             'upstream', CAPTURE_STATE.upstream, ...
             'caller', caller); %#ok<NASGU>
info = whos('rec');

k = CAPTURE_STATE.nrec(name);
status = 'saved';
if info.bytes > CAPTURE_STATE.maxBytes
    status = 'too_large';
else
    d = fullfile(CAPTURE_STATE.dir, name);
    if ~exist(d, 'dir')
        mkdir(d);
    end
    save(fullfile(d, sprintf('call_%03d.mat', k)), 'rec', '-v7');
end
CAPTURE_STATE.log{end+1} = sprintf('%s,%d,%d,%s,%s', name, k, info.bytes, status, caller);
end
