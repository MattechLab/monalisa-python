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
- Tutorial 1 end to end: [examples/tutorial_1/tutorial_1.py](examples/tutorial_1/tutorial_1.py).

The iterative reconstructions (Sensa, Steva, Sleva, Teva/Sensitiva-Morphosia) come next.
Interactive steps of the MATLAB version (dialogs, ROI drawing) are parameters in Python; the
MATLAB image viewers are not ported. Live status: [PORTING_STATUS.md](PORTING_STATUS.md).

## Install

```bash
pip install -e ".[dev,io]"     # numpy, scipy, numba, h5py, twixtools, ismrmrd (+ pytest, ruff)
```

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
python examples/tutorial_1/tutorial_1.py --data monalisa/demo/data_demo/data_8_tutorial_1 --out results
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
