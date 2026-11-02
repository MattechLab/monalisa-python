function imregdemons_reference(out_file)
% Reference registrations with MATLAB's imregdemons, used to validate the
% open-source (SimpleITK) replacement in monalisa.imReg._demons.
% Synthetic images warped by known smooth displacement fields, 2D and 3D,
% registered with the iteration schedule of bmImDeformField*_imRegDemons23
% ([n, fix(n/2), fix(n/4)], 3 pyramid levels) and with a single level.

rng(0);
cases = {};

% 2D: Shepp-Logan phantom, smooth sinusoidal deformation (max ~3 px)
N = 128;
fixed = 255*mat2gray(imgaussfilt(phantom(N), 1));
[X, Y] = meshgrid(1:N, 1:N);
D_true = cat(3, 3*sin(2*pi*Y/N).*cos(pi*X/N), 2*cos(2*pi*X/N));
moving = imwarp(fixed, D_true);  % moving(p) = fixed(p + D_true(p))
cases{end+1} = private_case('phantom2d', moving, fixed, [50, 25, 12], D_true);
cases{end+1} = private_case('phantom2d_1level', moving, fixed, 20, D_true);

% 2D: random smooth texture, larger deformation (max ~5 px), odd size (padding)
N2 = [100, 90];
fixed = 255*mat2gray(imgaussfilt(rand(N2), 3));
[X, Y] = meshgrid(1:N2(2), 1:N2(1));
D_true = cat(3, 5*sin(pi*Y/N2(1)), 4*sin(2*pi*X/N2(2)).*sin(pi*Y/N2(1)));
moving = imwarp(fixed, D_true);
cases{end+1} = private_case('texture2d', moving, fixed, [40, 20, 10], D_true);

% 3D: ellipsoids, smooth deformation (max ~3 voxels)
N3 = 48;
[X, Y, Z] = meshgrid(1:N3, 1:N3, 1:N3);
c = (N3+1)/2;
fixed = 200*((X-c).^2/18^2 + (Y-c).^2/14^2 + (Z-c).^2/16^2 < 1) ...
      + 55*((X-c-6).^2 + (Y-c).^2 + (Z-c+3).^2 < 6^2);
fixed = imgaussfilt3(fixed, 1);
D_true = cat(4, 3*sin(2*pi*Z/N3), 2*cos(2*pi*X/N3), 2*sin(2*pi*Y/N3));
moving = imwarp(fixed, D_true);
cases{end+1} = private_case('ellipsoids3d', moving, fixed, [30, 15, 7], D_true);
cases{end+1} = private_case('ellipsoids3d_1level', moving, fixed, 20, D_true);

save(out_file, 'cases', '-v7');
end

function s = private_case(name, moving, fixed, iterations, D_true)
moving = single(moving);
fixed  = single(fixed);
[D, moving_reg] = imregdemons(moving, fixed, iterations, 'PyramidLevels', numel(iterations), ...
                              'DisplayWaitbar', false);
s = struct('name', name, 'moving', moving, 'fixed', fixed, 'iterations', iterations, ...
           'D_true', D_true, 'D', D, 'moving_reg', moving_reg);
end
