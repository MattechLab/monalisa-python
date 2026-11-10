function y = capture_to_plain(x)
% y = capture_to_plain(x)
%
% Recursively convert x to plain MATLAB data (numeric, logical, char, cell,
% struct) that can be saved in a -v7 MAT-file and read by scipy.io.loadmat.
% Objects become structs with an extra field 'matlabClass'.

if iscell(x)
    y = cell(size(x));
    for i = 1:numel(x)
        y{i} = capture_to_plain(x{i});
    end
elseif isstring(x)
    if isscalar(x)
        y = char(x);
    else
        y = cellstr(x);
    end
elseif isa(x, 'function_handle')
    y = struct('matlabClass', 'function_handle', 'value', func2str(x));
elseif isa(x, 'containers.Map')
    y = struct('matlabClass', 'containers.Map', ...
               'keys', {capture_to_plain(keys(x))}, ...
               'values', {capture_to_plain(values(x))});
elseif isobject(x)
    cls = class(x);
    if numel(x) ~= 1
        c = cell(size(x));
        for i = 1:numel(x)
            c{i} = capture_to_plain(x(i));
        end
        y = struct('matlabClass', 'objectArray', 'elementClass', cls, 'elements', {c});
        return;
    end
    w = warning('off', 'MATLAB:structOnObject');
    s = struct(x);
    warning(w);
    y = struct('matlabClass', cls);
    fn = fieldnames(s);
    for i = 1:numel(fn)
        y.(fn{i}) = capture_to_plain(s.(fn{i}));
    end
elseif isstruct(x)
    y = x;
    fn = fieldnames(x);
    for j = 1:numel(x)
        for i = 1:numel(fn)
            y(j).(fn{i}) = capture_to_plain(x(j).(fn{i}));
        end
    end
else
    y = x;
end
end
