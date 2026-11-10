# Validation: tutorial 1 end to end (Python port vs MATLAB)

Run on 2026-10-30 with upstream Monalisa `0cb5cf9`, MATLAB R2024b and the
tutorial 1 data (3D radial phyllotaxis brain scan, 42 channels, Siemens raw data).

- MATLAB: `tools/matlab_capture/scenarios/scenario_tutorial_recon.m`
- Python: `examples/tutorial_1/tutorial_1.py`
- Comparison: `tests/e2e/test_tutorial_1.py` (`monalisa.testing.metrics`)

Both pipelines run coil sensitivity estimation (automatic mask, 5 refinement iterations), binning
(all lines and 5 s sequential windows), mitosius preparation (normalization with the same fixed ROI
in place of the interactive `roipoly`), and gridded reconstructions with `mathilda` (`bmMathilda`).

| Output | relative L2 | NMSE | SSIM (magnitude) |
|---|---:|---:|---:|
| Binning masks (all lines, sequential 5 s) | identical | | |
| Coil sensitivity maps C (48³ × 42) | 9.7e-05 | 9.3e-09 | 0.999999996 |
| Volume elements (3D Voronoi, all lines) | 4.1e-14 | | |
| Gridded image used for normalization (80³) | 6.7e-05 | 4.6e-09 | 0.999999995 |
| Normalization value | 6.1e-05 (relative difference) | | |
| x0: gridded reconstruction, all lines (80³) | 3.8e-05 | 1.5e-09 | 0.999999998 |
| x1: sequential bin 1 (80³) | 4.1e-05 | 1.7e-09 | 0.999999998 |
| x1: sequential bin 2 (80³) | 4.1e-05 | 1.7e-09 | 0.999999998 |
| x1: sequential bin 3 (80³) | 4.1e-05 | 1.7e-09 | 0.999999998 |
| x1: sequential bin 4 (80³) | 4.1e-05 | 1.7e-09 | 0.999999998 |
| x1: sequential bin 5 (80³) | 4.1e-05 | 1.7e-09 | 0.999999998 |
| x1: sequential bin 6 (80³) | 4.1e-05 | 1.7e-09 | 0.999999998 |
| x1: sequential bin 7 (80³) | 4.1e-05 | 1.7e-09 | 0.999999998 |
| x1: sequential bin 8 (80³) | 4.1e-05 | 1.7e-09 | 0.999999998 |

All differences are at the level of single-precision rounding (the whole pipeline computes in
single precision, like MATLAB). For reference, the previous port (2026 master project) reported
relative L2 = 4.3 and SSIM = 0.18 on x0 and 0.14 / 0.93 on C.

Runtime on the development workstation (36 cores, 125 GB): Python 8.5 min, peak memory 35 GB;
MATLAB 11.7 min (including the recording overhead of the capture harness).
