function scenario_volume_elements(ctx) %#ok<INUSD>
% Capture scenario: bmVolumeElement on synthetic trajectories of every
% supported type (small sizes), and bmMathilda on some of them.
rng(0);
FoV = 240; dK = 1/FoV; N = 32;

% 2D Cartesian grid, slightly rotated
[kx, ky] = ndgrid((-N/2:N/2-1)*dK, (-N/2:N/2-1)*dK);
R = [cos(0.1), -sin(0.1); sin(0.1), cos(0.1)];
t = R*[kx(:)'; ky(:)'];
ve = bmVolumeElement(t, 'cartesian2'); %#ok<NASGU>

% 2D random points in a box
t = (rand(2, 400) - 0.5) * N * dK;
ve = bmVolumeElement(t, 'voronoi_box2', [N, N], [dK, dK]); %#ok<NASGU>

% 2D center-out radial (each line starts at the center)
nLine = 24;
r = (0:N/2-1)*dK;
phi = 2*pi*(0:nLine-1)/nLine + 0.05;
t = cat(1, reshape(r(:)*cos(phi), [1, N/2, nLine]), reshape(r(:)*sin(phi), [1, N/2, nLine]));
ve = bmVolumeElement(t, 'voronoi_center_out_radial2'); %#ok<NASGU>

% 3D full radial phyllotaxis and center-out radial
p = bmMriAcquisitionParam([]);
p.N = N; p.nSeg = 8; p.nShot = 12; p.FoV = FoV; p.selfNav_flag = true; p.nShot_off = 2;
t3 = bmTraj_fullRadial3_phyllotaxis_lineAssym2(p);
ve = bmVolumeElement(t3, 'full_radial3'); %#ok<NASGU>
ve = bmVolumeElement(t3, 'voronoi_full_radial3');
y = single(randn(4, numel(t3)/3) + 1i*randn(4, numel(t3)/3));
x = bmMathilda(y, t3, ve, [], [N, N, N], [N, N, N], [dK, dK, dK]); %#ok<NASGU>
t3co = t3(:, N/2+1:end, :);
ve = bmVolumeElement(t3co, 'center_out_radial3'); %#ok<NASGU>

% random partial Cartesian along x (2D and 3D)
nL = 20;
ky = (randperm(N, nL) - N/2 - 1)*dK;
[kx2, ky2] = ndgrid((-N/2:N/2-1)*dK, ky);
t = [kx2(:)'; ky2(:)'];
ve = bmVolumeElement(t, 'randomPartialCartesian2_x', [N, N], [dK, dK]); %#ok<NASGU>
yz = (rand(2, nL) - 0.5) * N * dK;
kx3 = repmat((-N/2:N/2-1)'*dK, [1, nL]);
t = cat(1, reshape(kx3, [1, N, nL]), reshape(repmat(yz(1, :), [N, 1]), [1, N, nL]), ...
           reshape(repmat(yz(2, :), [N, 1]), [1, N, nL]));
ve = bmVolumeElement(t, 'randomPartialCartesian3_x', [N, N, N], [dK, dK, dK]); %#ok<NASGU>
end
