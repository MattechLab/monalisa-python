function tf = capture_should_record(name, args)
% tf = capture_should_record(name, args)
%
% Decide whether the current call of function name is recorded. The first
% CAPTURE_STATE.firstK calls are always recorded, later calls only when their
% input signature (classes and sizes) has not been seen yet, up to
% CAPTURE_STATE.maxPerFunc records per function.

global CAPTURE_STATE
tf = false;
if isempty(CAPTURE_STATE) || ~CAPTURE_STATE.enabled
    return;
end

if isKey(CAPTURE_STATE.seen, name)
    nSeen = CAPTURE_STATE.seen(name) + 1;
else
    nSeen = 1;
    CAPTURE_STATE.sigs(name) = {};
    CAPTURE_STATE.nrec(name) = 0;
end
CAPTURE_STATE.seen(name) = nSeen;

if CAPTURE_STATE.nrec(name) >= CAPTURE_STATE.maxPerFunc || nSeen > CAPTURE_STATE.maxSeen
    return;
end

sig = capture_signature(args);
sigs = CAPTURE_STATE.sigs(name);
if nSeen <= CAPTURE_STATE.firstK || ~any(strcmp(sig, sigs))
    tf = true;
    CAPTURE_STATE.sigs(name) = [sigs, {sig}];
    CAPTURE_STATE.nrec(name) = CAPTURE_STATE.nrec(name) + 1;
end
end


function sig = capture_signature(args)
parts = cell(1, numel(args));
for i = 1:numel(args)
    a = args{i};
    s = sprintf('%s[%s]', class(a), num2str(size(a)));
    if iscell(a) && ~isempty(a)
        s = [s, '{', class(a{1}), '[', num2str(size(a{1})), ']}'];
    end
    if isreal(a) == false
        s = [s, 'c'];
    end
    parts{i} = s;
end
sig = strjoin(parts, ';');
end
