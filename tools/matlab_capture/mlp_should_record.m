function tf = mlp_should_record(name, args)
% tf = mlp_should_record(name, args)
%
% Decide whether the current call of function name is recorded. The first
% MLP_STATE.firstK calls are always recorded, later calls only when their
% input signature (classes and sizes) has not been seen yet, up to
% MLP_STATE.maxPerFunc records per function.

global MLP_STATE
tf = false;
if isempty(MLP_STATE) || ~MLP_STATE.enabled
    return;
end

if isKey(MLP_STATE.seen, name)
    nSeen = MLP_STATE.seen(name) + 1;
else
    nSeen = 1;
    MLP_STATE.sigs(name) = {};
    MLP_STATE.nrec(name) = 0;
end
MLP_STATE.seen(name) = nSeen;

if MLP_STATE.nrec(name) >= MLP_STATE.maxPerFunc || nSeen > MLP_STATE.maxSeen
    return;
end

sig = mlp_signature(args);
sigs = MLP_STATE.sigs(name);
if nSeen <= MLP_STATE.firstK || ~any(strcmp(sig, sigs))
    tf = true;
    MLP_STATE.sigs(name) = [sigs, {sig}];
    MLP_STATE.nrec(name) = MLP_STATE.nrec(name) + 1;
end
end


function sig = mlp_signature(args)
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
