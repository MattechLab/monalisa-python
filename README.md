# monalisa-python

Python port of [Monalisa](https://github.com/MattechLab/monalisa), the MattechLab toolbox for
non-Cartesian and Cartesian MRI reconstruction, developed within the HES-SO Open Research Data
programme (2026).

The port is **faithful first**: every upstream MATLAB function `bmFoo` of `src/` becomes
`monalisa/<same folder>/bmFoo.py` with the same name, the same argument order, the same array
shapes (column-major) and the same precision (`single` → float32/complex64). Each ported function
is validated against **golden recordings** of the MATLAB implementation (see
[docs/porting_method.md](docs/porting_method.md)).

## Install

```bash
pip install -e ".[dev]"          # numpy, scipy, numba (+ pytest, ruff)
```

## Quick example: gridded reconstruction

```python
import scipy.io as sio
import monalisa as ml

d = sio.loadmat("data_2_static_radial_simulated_from_cartesian/data.mat")
ve = ml.bmVolumeElement(d["t"], "voronoi_full_radial2")
C = ml.bmImResize(d["C"], [32, 32], d["frSize"])
x0 = ml.bmMathilda(d["y"], d["t"], ve, C, d["N_u"], d["frSize"], d["dK_u"])
```

## Status

See [PORTING_STATUS.md](PORTING_STATUS.md). The first milestone is the gridded reconstruction
(`bmMathilda`) and its dependencies; the iterative reconstructions follow.

## Tests

```bash
pytest                       # unit tests + replay of all MATLAB recordings found in fixtures/
```

MATLAB recordings are produced with `tools/matlab_capture` (requires MATLAB and the upstream
repository):

```bash
matlab -batch "addpath('tools/matlab_capture'); run_capture('static2d', fullfile(pwd,'fixtures','matlab'), '/path/to/monalisa')"
```

## License

Apache License 2.0, see [LICENSE](LICENSE).
