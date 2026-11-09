# monalisa-python

Python port of [Monalisa](https://github.com/MattechLab/monalisa), the MattechLab toolbox for
non-Cartesian and Cartesian MRI reconstruction, developed within the HES-SO Open Research Data
programme (2026).

The port is **faithful first**: every upstream MATLAB function `bmFoo` of `src/` becomes
`monalisa/<same folder>/bmFoo.py` with the same name, the same argument order, the same array
shapes (column-major) and the same precision (`single` → float32/complex64). Each ported function
is validated against **golden recordings of the MATLAB implementation**; see
[docs/porting_method.md](docs/porting_method.md) and [CONVENTIONS.md](CONVENTIONS.md).

## What works

- **Gridded reconstruction** `bmMathilda` (1D/2D/3D, with or without coil combination, cropping),
  the numba port of the gridding MEX kernels and the deapodization `bmK`.
- **Sparse gridding operators** `bmTraj2SparseMat` (`Gn`, `Gu`, `Gut`), `bmSparseMat`,
  forward/adjoint non-Cartesian Fourier operators `bmShanna` / `bmNakatsha`, `bmNasha`.
- **Trajectories and volume elements**: 3D phyllotaxis radial, Voronoi full/center-out radial
  2D/3D, Cartesian, Voronoi box, random partial Cartesian.
- **Raw data**: Siemens twix `.dat` (via `twixtools`) and ISMRMRD `.mrd` readers with automatic
  steady-state detection.
- **Coil sensitivity estimation** from body + surface coil scans (automatic mask).
- **Binning and mitosius** (data split into bins, MATLAB-compatible v7.3 files in both directions).
- **Iterative reconstructions**: Sensa, Steva, Sleva; chain reconstructions TevaMorphosia,
  TevaDuoMorphosia and SensitivaMorphosia, with or without deformation matrices.
- **Demons registration** for motion-compensated reconstructions
  (`bmImDeformFieldChain_imRegDemons23`, `bmImDeformFieldSheet_imRegDemons23`): MATLAB's
  `imregdemons` is replaced by SimpleITK's demons, so no MATLAB licence is needed; see
  [docs/validation_registration.md](docs/validation_registration.md).
- Tutorial 1 end to end: [examples/tutorial_1/tutorial_1.ipynb](examples/tutorial_1/tutorial_1.ipynb)
  (notebook with figures) or [tutorial_1.py](examples/tutorial_1/tutorial_1.py) (script).

- Image viewer and interactive steps: see below.

Live status: [PORTING_STATUS.md](PORTING_STATUS.md).

## Install

With pip (any Python environment, 3.10 or newer):

```bash
git clone https://github.com/MattechLab/monalisa-python.git
cd monalisa-python
pip install -e ".[io,reg]"            # numpy, scipy, numba, napari + raw-data readers + SimpleITK (registration)
pip install -e ".[io,reg,notebook]"   # + JupyterLab, for the tutorial notebook
pip install -e ".[dev,io]"            # + pytest, ruff (development)
```

With conda (everything inside the environment, no admin rights needed):

```bash
conda create -n monalisa -c conda-forge python=3.12 matplotlib-base xcb-util-cursor
conda activate monalisa
pip install -e ".[io,reg,notebook]"
```

The package installs as `monalisa-python` and is imported as `monalisa`.

**Linux: library for the Qt windows.** The napari viewer and the interactive steps use Qt, which
on Linux with X11 needs the library libxcb-cursor (not available from pip). Either:

- in a conda environment: `conda install -c conda-forge xcb-util-cursor` (monalisa loads it from
  the environment), or
- system-wide: `sudo apt install libxcb-cursor0` (Debian, Ubuntu) or
  `sudo dnf install xcb-util-cursor` (Fedora).

Without it, opening a window raises an error that says so; the notebook viewer works without it.
In a conda environment, install `matplotlib-base`, not conda's `matplotlib`: the latter brings
PySide6 with a second copy of Qt, whose libraries clash with napari's (PyQt6) and crash Python as
soon as a window opens.

## Viewing images and interactive steps

`bmImage` shows 2D to 5D images (or a list of frames) like the MATLAB viewer, with the MATLAB
axis order: `x(:, :, k)` with x down the rows, and sliders for z and time. Outside Jupyter it opens
a [napari](https://napari.org) window (views along x/y/z, contrast, 3D rendering, points);
inside Jupyter it shows sliders under the cell (`backend="napari"` opens the window instead).
`render3d=True` opens the napari window in 3D (volume rendering, rotate with the mouse), from a
script or from a notebook; the window stays responsive while the notebook runs.
`layout="orthogonal"` opens one window laid out like ITK-SNAP: the slices along z, x and y and the
3D view (bottom left), linked by a cursor with a crosshair (click in a slice view to move it), with
one time slider and one contrast setting for all views.

```python
import monalisa as ml
ml.bmImage(x_cs)                 # list of 3D frames -> x, y, z, t
ml.bmImage(x_cs, render3d=True)  # napari window in 3D, slider on t (also from Jupyter)
ov = ml.bmImage(x_cs, layout="orthogonal")  # 3 slices + 3D, like ITK-SNAP
ov.set_point([40, 36, 41, 0])    # move the cursor from code (0-based x, y, z, t); ov.point reads it
ml.bmImage(x0, block=True)       # in a script: keep the window open until closed (or napari.run())
mask = ml.roipoly(x0[:, :, 40])  # draw a polygon, like MATLAB roipoly
```

As in MATLAB, `autoFlag=False` opens windows where the automatic choices can be checked and
changed: the acquisition parameters (raw data readers), the coil-mask thresholds and the bounding
box (`bmCoilSense_nonCart_mask_automatic`). Every value chosen in a window is printed and can be
set in the code instead, which needs no window and is reproducible:

| Window | Set it in the code |
|---|---|
| metadata check (`createRawDataReader(f, False)`) | `createRawDataReader(f, True)`, then `reader.acquisitionParams.nShot_off = 14` (any field) |
| coil-mask thresholds and box | `bmCoilSense_nonCart_mask_automatic(y, Gn, True, th_RMS, th_MIP, borders)` |
| normalization ROI (`roipoly(im)`) | `roipoly(im, c, r)` with the printed vertices, or any boolean mask |

## Reading MATLAB .mat files

```python
import scipy.io as sio
d = sio.loadmat("data.mat")        # MATLAB -v7 and older (the default of MATLAB save)

from monalisa.readWrite._mat73 import loadmat73
r = loadmat73("reconstructions.mat")   # -v7.3 (HDF5): large files, and the files written here
```

`loadmat` returns MATLAB logical arrays as `uint8`: convert masks with `.astype(bool)` before
indexing with them.

## Example: gridded reconstruction of a 2D radial acquisition

```python
import scipy.io as sio
import monalisa as ml

d = sio.loadmat("monalisa/demo/data_demo/data_2_static_radial_simulated_from_cartesian/data.mat")
ve = ml.bmVolumeElement(d["t"], "voronoi_full_radial2")
C = ml.bmImResize(d["C"], [32, 32], d["frSize"])
x0 = ml.bmMathilda(d["y"], d["t"], ve, C, d["N_u"], d["frSize"], d["dK_u"])
```

Tutorial 1 (3D radial brain scan, Siemens raw data):

```bash
python demo/data_demo/data_8_tutorial_1/download_data.py   # raw data, about 7.9 GB (once)
jupyter lab examples/tutorial_1/tutorial_1.ipynb           # or:
python examples/tutorial_1/tutorial_1.py --data demo/data_demo/data_8_tutorial_1 --out results
```

## Tests

```bash
pytest                       # unit tests + replay of all MATLAB recordings found in fixtures/matlab
```

MATLAB recordings are produced with `tools/matlab_capture` (requires MATLAB and the upstream
repository at the commit in `monalisa.UPSTREAM_COMMIT`):

```bash
matlab -batch "addpath('tools/matlab_capture'); run_capture('static2d', fullfile(pwd,'fixtures','matlab'), '/path/to/monalisa')"
```

Scenarios: `static2d`, `volume_elements`, `tutorial_coilsense`, `ismrmrd`, `tutorial_recon`
(see `tools/matlab_capture/scenarios`). The end-to-end comparison of tutorial 1 is opt-in:
`MONALISA_E2E_DATA=/path/to/data_8_tutorial_1 pytest tests/e2e -s`.

## License

Apache License 2.0, see [LICENSE](LICENSE).
