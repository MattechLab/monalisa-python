function scenario_ismrmrd(ctx)
% Capture scenario: ISMRMRD reader on fixtures/data/bodyCoil.mrd
% (made with tools/make_test_mrd.py from the tutorial body coil scan).
here = fileparts(mfilename('fullpath'));
f = fullfile(here, '..', '..', '..', 'fixtures', 'data', 'bodyCoil.mrd');
reader = createRawDataReader(f, true);
reader.acquisitionParams.traj_type = 'full_radial3_phylotaxis';
y = reader.readRawData(true, true); %#ok<NASGU>
y = reader.readRawData(false, false); %#ok<NASGU>
end
