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

```bash
git clone https://github.com/MattechLab/monalisa-python.git
cd monalisa-python
pip install -e ".[io,reg]"            # numpy, scipy, numba, napari + raw-data readers + SimpleITK (registration)
pip install -e ".[io,reg,notebook]"   # + JupyterLab, for the tutorial notebook
pip install -e ".[dev,io]"            # + pytest, ruff (development)
```

The package installs as `monalisa-python` and is imported as `monalisa`.

## Viewing images and interactive steps

`bmImage` shows 2D to 5D images (or a list of frames) like the MATLAB viewer, with the MATLAB
axis order: `x(:, :, k)` with x down the rows, and sliders for z and time. Outside Jupyter it opens
a [napari](https://napari.org) window (views along x/y/z, contrast, 3D rendering, points);
inside Jupyter it shows sliders under the cell (`backend="napari"` opens the window instead).

```python
import monalisa as ml
ml.bmImage(x_cs)                 # list of 3D frames -> x, y, z, t
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
