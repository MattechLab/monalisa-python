function kind = capture_file_kind(txt)
% kind = capture_file_kind(txt)
%
% Return 'function', 'classdef' or 'script' for the content of a .m file,
% based on its first code keyword (comments and block comments skipped).

txt = regexprep(txt, '^[ \t]*%\{.*?^[ \t]*%\}', '', 'lineanchors');
lines = splitlines(txt);
kind = 'script';
for i = 1:numel(lines)
    l = strtrim(lines{i});
    if isempty(l) || l(1) == '%'
        continue;
    end
    w = regexp(l, '^\w+', 'match', 'once');
    if strcmp(w, 'function')
        kind = 'function';
    elseif strcmp(w, 'classdef')
        kind = 'classdef';
    end
    return;
end
end
