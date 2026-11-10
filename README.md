# monalisa-python

Python port of [Monalisa](https://github.com/MattechLab/monalisa), the MattechLab toolbox for
non-Cartesian and Cartesian MRI reconstruction, developed within the HES-SO Open Research Data
programme (2026).

The port is **faithful first**: every ported MATLAB function keeps its arguments, array shapes
(column-major) and precision (`single` → float32/complex64), and is validated against **golden
recordings of the MATLAB implementation**; see [docs/porting_method.md](docs/porting_method.md) and
[CONVENTIONS.md](CONVENTIONS.md). The names follow Python conventions, without the authors'
initials of the MATLAB names: `bmMathilda` → `monalisa.recon.mathilda`, `bmSparseMat` →
`monalisa.sparse.SparseMat`. The table of all names is [docs/renaming.md](docs/renaming.md).

## Install

With pip (any Python environment, 3.10 or newer):

```bash
git clone https://github.com/MattechLab/monalisa-python.git
cd monalisa-python
pip install -e ".[io,reg]"            # numpy, scipy, numba, h5py, napari + raw-data readers + SimpleITK (registration)
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
soon as a window opens. For the same reason, in a conda environment monalisa starts Qt with its
built-in theme (`QT_QPA_PLATFORMTHEME=generic`) instead of the GTK one, which would load the
system's GLib next to conda's; set `QT_QPA_PLATFORMTHEME` yourself to choose another.

## Package layout

| Subpackage | Contents |
|---|---|
| `monalisa.recon` | reconstructions: gridded `mathilda`, `nasha`; iterative `sensa` (SENSE), `sleva` (L2), `steva` (TV); chains `teva_morphosia_chain`, `teva_duo_morphosia_chain`, `sensitiva_morphosia_chain` (temporal TV / L2, optionally motion-compensated) |
| `monalisa.io` | raw data readers (`create_raw_data_reader`, `SiemensReader`, `IsmrmrdReader`), acquisition parameters, MATLAB v7.3 files (`loadmat73`, `savemat73`) |
| `monalisa.trajectory` | trajectories (`traj`, 3D phyllotaxis radial), grid size and step, line format, `low_res` |
| `monalisa.geometry` | volume elements (density compensation), Voronoi cells |
| `monalisa.gridding` | gridding (`gridder_n2u_leight`), sparse gridding matrices (`traj_to_sparse_mat`), deformation matrices |
| `monalisa.sparse` | Monalisa's sparse matrix `SparseMat` and its products |
| `monalisa.fourier` | centered DFTs, deapodization, forward/adjoint non-Cartesian Fourier model (`shanna`, `nakatsha`) |
| `monalisa.coil` | coil sensitivity estimation (`coil_sense_non_cart_*`), coil combination |
| `monalisa.binning` | binning of the lines (`mitosis`), binned data on disk (`mitosius_create`, `mitosius_load`) |
| `monalisa.image` | crop, zero fill, resize, deformation, Laplace/diffusion smoothing, `rms`, `mip` |
| `monalisa.registration` | demons deformation fields between frames |
| `monalisa.optim` | building blocks of the iterative reconstructions (gradients, norms, proximal operators, `WitnessInfo`) |
| `monalisa.display` | image viewer `show_image`, polygon masks `roipoly` |
| `monalisa.array`, `monalisa.util` | array formats (block, column, point), cells; argument defaults, clock |

Every public function and class is also available from the top-level package
(`import monalisa as ml; ml.mathilda(...)`). `ml.find_function("bmMathilda")` returns the Python
function of a MATLAB name.

## What works

- **Gridded reconstruction** `mathilda` (1D/2D/3D, with or without coil combination, cropping),
  the numba port of the gridding MEX kernels and the deapodization.
- **Sparse gridding operators** `traj_to_sparse_mat` (`Gn`, `Gu`, `Gut`), `SparseMat`,
  forward/adjoint non-Cartesian Fourier operators `shanna` / `nakatsha`, `nasha`.
- **Trajectories and volume elements**: 3D phyllotaxis radial, Voronoi full/center-out radial
  2D/3D, Cartesian, Voronoi box, random partial Cartesian.
- **Raw data**: Siemens twix `.dat` (via `twixtools`) and ISMRMRD `.mrd` readers with automatic
  steady-state detection.
- **Coil sensitivity estimation** from body + surface coil scans (automatic mask).
- **Binning and mitosius** (data split into bins, MATLAB-compatible v7.3 files in both directions).
- **Iterative reconstructions**: Sensa, Steva, Sleva; chain reconstructions TevaMorphosia,
  TevaDuoMorphosia and SensitivaMorphosia, with or without deformation matrices.
- **Demons registration** for motion-compensated reconstructions
  (`im_deform_field_chain_im_reg_demons23`, `im_deform_field_sheet_im_reg_demons23`): MATLAB's
  `imregdemons` is replaced by SimpleITK's demons, so no MATLAB licence is needed; see
  [docs/validation_registration.md](docs/validation_registration.md).
- Tutorial 1 end to end: [examples/tutorial_1/tutorial_1.ipynb](examples/tutorial_1/tutorial_1.ipynb)
  (notebook with figures) or [tutorial_1.py](examples/tutorial_1/tutorial_1.py) (script).
- Image viewer and interactive steps: see below.

Live status: [PORTING_STATUS.md](PORTING_STATUS.md).

## Viewing images and interactive steps

`show_image(x, view)` shows 2D to 5D images (or a list of frames) like the MATLAB viewer
`bmImage`, with the MATLAB axis order: `x(:, :, k)` with x down the rows, and sliders for z and
time.

| `view` | Shows | Where |
|---|---|---|
| `"inline"` | sliders and the slice below the cell | Jupyter (default there) |
| `"window"` | a [napari](https://napari.org) window: one slice view, views along x/y/z, contrast, points | anywhere (default outside Jupyter) |
| `"3d"` | the same window, opened in 3D (volume rendering, rotate with the mouse) | anywhere |
| `"ortho"` | one window laid out like ITK-SNAP: slices along z, x, y and the 3D view, linked by a cursor (click in a slice view to move it) | anywhere |

The windows also open from Jupyter, next to the notebook. Other parameters: `name` (title),
`contrast=(low, high)`, `block=True` (in a script, keep the window open until it is closed; not
needed in Jupyter) and `viewer` (add the image to an earlier `"window"` / `"3d"` window to compare
reconstructions: side by side in one row, in the order added, with shared sliders; the grid button at the
bottom left stacks them instead).

```python
import monalisa as ml
ml.show_image(x_cs)                         # list of 3D frames -> x, y, z, t
ml.show_image(x_cs, "3d", name="TevaMorphosia")
ov = ml.show_image(x_cs, "ortho")           # 3 slices + 3D, like ITK-SNAP
ov.set_point([40, 36, 41, 0])               # move the cursor from code (0-based x, y, z, t); ov.point reads it
v = ml.show_image(x_sensa, "window", name="Sensa")
ml.show_image(x_cs, viewer=v, name="TevaMorphosia")   # same window, side by side: Sensa left, CS right
ml.show_image(x0, "window", block=True)     # in a script: keep the window open until closed
mask = ml.roipoly(x0[:, :, 40])             # draw a polygon, like MATLAB roipoly
```

As in MATLAB, `autoFlag=False` opens windows where the automatic choices can be checked and
changed: the acquisition parameters (raw data readers), the coil-mask thresholds and the bounding
box (`coil_sense_non_cart_mask_automatic`). Every value chosen in a window is printed and can be
set in the code instead, which needs no window and is reproducible:

| Window | Set it in the code |
|---|---|
| metadata check (`create_raw_data_reader(f, False)`) | `create_raw_data_reader(f, True)`, then `reader.acquisitionParams.nShot_off = 14` (any field) |
| coil-mask thresholds and box | `coil_sense_non_cart_mask_automatic(y, Gn, True, th_RMS, th_MIP, borders)` |
| normalization ROI (`roipoly(im)`) | `roipoly(im, c, r)` with the printed vertices, or any boolean mask |

## Reading MATLAB .mat files

```python
import scipy.io as sio
d = sio.loadmat("data.mat")        # MATLAB -v7 and older (the default of MATLAB save)

from monalisa.io import loadmat73
r = loadmat73("reconstructions.mat")   # -v7.3 (HDF5): large files, and the files written here
```

`loadmat` returns MATLAB logical arrays as `uint8`: convert masks with `.astype(bool)` before
indexing with them.

## Example: gridded reconstruction of a 2D radial acquisition

```python
import scipy.io as sio
import monalisa as ml

d = sio.loadmat("monalisa/demo/data_demo/data_2_static_radial_simulated_from_cartesian/data.mat")
ve = ml.volume_element(d["t"], "voronoi_full_radial2")
C = ml.im_resize(d["C"], [32, 32], d["frSize"])
x0 = ml.mathilda(d["y"], d["t"], ve, C, d["N_u"], d["frSize"], d["dK_u"])
```

Tutorial 1 (3D radial brain scan, Siemens raw data):

```bash
python demo/data_demo/data_8_tutorial_1/download_data.py   # raw data, about 7.9 GB (once)
jupyter lab examples/tutorial_1/tutorial_1.ipynb           # or:
python examples/tutorial_1/tutorial_1.py --data demo/data_demo/data_8_tutorial_1 --out results
python examples/tutorial_1/tutorial_1.py --out results --show   # view the saved results
```

## Tests

```bash
pytest                       # unit tests + replay of all MATLAB recordings found in fixtures/matlab
```

MATLAB recordings are produced with `tools/matlab_capture` (requires MATLAB and the upstream
repository at the commit in `monalisa.UPSTREAM_COMMIT`); they are stored under the MATLAB names
of the functions and replayed against their Python ports (`monalisa.MATLAB_NAMES`):

```bash
matlab -batch "addpath('tools/matlab_capture'); run_capture('static2d', fullfile(pwd,'fixtures','matlab'), '/path/to/monalisa')"
```

Scenarios: `static2d`, `volume_elements`, `tutorial_coilsense`, `ismrmrd`, `tutorial_recon`
(see `tools/matlab_capture/scenarios`). The end-to-end comparison of tutorial 1 is opt-in:
`MONALISA_E2E_DATA=/path/to/data_8_tutorial_1 pytest tests/e2e -s`.

## Credits

Monalisa, the MATLAB toolbox this package is ported from, is the work of the MattechLab team
(HES-SO Valais-Wallis, CHUV and UNIL): Bastien Milani (core code and mathematical formulation),
Mauro Leidi, Yiwei Jia, Jaime Barranco, Dominik Helbing, Jean-Baptiste Ledoux and Benedetta
Franceschiello (principal investigator); see the upstream
[acknowledgements](https://mattechlab.github.io/monalisa/). The upstream code was supported by the
Swiss National Science Foundation (grants 320030B_201292, 220433 and 229214). The Python port is
funded by the HES-SO Open Research Data programme. Authorship is recorded here and in the git
history rather than in the source files.

## License

Apache License 2.0, see [LICENSE](LICENSE).
