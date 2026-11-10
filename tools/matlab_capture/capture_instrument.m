function nWrapped = capture_instrument(srcDir, instrDir, excludeNames)
% nWrapped = capture_instrument(srcDir, instrDir, excludeNames)
%
% Copy the MATLAB source tree srcDir to instrDir and replace every function
% file NAME.m by a capture wrapper NAME.m that forwards to the renamed
% original NAME__orig.m and records inputs/outputs via capture_record.
%
% classdef files, scripts and the names listed in excludeNames are left
% untouched.

if nargin < 3
    excludeNames = {};
end

if exist(instrDir, 'dir')
    rmdir(instrDir, 's');
end
copyfile(srcDir, instrDir);

files = dir(fullfile(instrDir, '**', '*.m'));
nWrapped = 0;
for k = 1:numel(files)
    f = fullfile(files(k).folder, files(k).name);
    [folder, name] = fileparts(f);
    if any(strcmp(name, excludeNames))
        continue;
    end
    txt = fileread(f);
    if ~strcmp(capture_file_kind(txt), 'function')
        continue;
    end

    declExpr = ['^([ \t]*function[ \t]*(?:(\[[^\]]*\]|\w+)[ \t]*=[ \t]*)?)', name, '\>'];
    tok = regexp(txt, declExpr, 'tokens', 'once', 'lineanchors');
    if isempty(tok)
        warning('capture:noDecl', 'No main declaration found for %s, not wrapped.', name);
        continue;
    end
    nDecl = private_count_outputs(tok);

    origTxt = regexprep(txt, declExpr, ['$1', name, '__orig'], 'once', 'lineanchors');
    private_write([folder, filesep, name, '__orig.m'], origTxt);
    private_write(f, private_wrapper(name, nDecl));
    nWrapped = nWrapped + 1;
end

end


function nDecl = private_count_outputs(tok)
outTxt = '';
if numel(tok) >= 2
    outTxt = tok{2};
end
outTxt = regexprep(outTxt, '\.\.\.[^\n]*\n', ' ');
outTxt = strtrim(regexprep(outTxt, '[\[\],]', ' '));
if isempty(outTxt)
    nDecl = 0;
    return;
end
names = strsplit(outTxt);
if any(strcmp(names, 'varargout'))
    nDecl = -numel(names);
else
    nDecl = numel(names);
end
end


function txt = private_wrapper(name, nDecl)
L = {
    sprintf('function varargout = %s(varargin)', name)
    sprintf('%% capture wrapper (auto-generated). Original: %s__orig', name)
    sprintf('capture_rec_flag = capture_should_record(''%s'', varargin);', name)
    'capture_nCall = nargout;'
    sprintf('if capture_nCall == 0 && %d > 0', nDecl)
    '    capture_nCall = 1;'
    'end'
    'if capture_rec_flag'
    '    capture_in = capture_to_plain(varargin);'
    'end'
    'if capture_nCall == 0'
    sprintf('    %s__orig(varargin{:});', name)
    '    varargout = {};'
    'else'
    sprintf('    [varargout{1:capture_nCall}] = %s__orig(varargin{:});', name)
    'end'
    'if capture_rec_flag'
    sprintf('    capture_record(''%s'', capture_in, varargout, nargin, capture_nCall);', name)
    'end'
    'end'
    };
txt = strjoin(L, newline);
end


function private_write(f, txt)
fid = fopen(f, 'w');
if fid < 0
    error('capture:write', 'Cannot write %s', f);
end
fwrite(fid, txt);
fclose(fid);
end
