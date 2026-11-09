# Porting method: oracle-first, function by function

This repository ports Monalisa with a pipeline that can be reused for other MATLAB code bases.
Its core idea: **the scarce resource is not translated code but a trustworthy oracle.** Before a
function is translated, the MATLAB implementation is run on realistic inputs and its inputs and
outputs are recorded; the Python function is accepted only when it reproduces these recordings.

```
            upstream MATLAB (pinned commit)
                       │
   1. inventory ──────►│ tools/upstream_graph.py      static call graph, porting scope & order
                       │
   2. golden capture ─►│ tools/matlab_capture/         instrument src/, run scenarios, record calls
                       ▼
          fixtures/matlab/<scenario>/<function>/call_NNN.mat
                       │
   3. port ───────────►│ src/monalisa/<folder>/bmFoo.py   (CONVENTIONS.md; human or coding agent)
                       │
   4. verify ─────────►│ tests/parity (replay)  +  unit / property tests
                       │
   5. report ─────────►│ tools/port_status.py → PORTING_STATUS.md
                       ▼
   6. sync: new upstream commit → re-capture → fixture diff → functions to re-port
```

## 1. Inventory and scope

`tools/upstream_graph.py` parses all `.m` files, builds the static call graph and computes the
closure of the demo pipelines (tutorial 1, static/chain/sheet reconstructions): 175 functions of
`src/`. Functions are ported leaves first, so that every port is testable with ported callees.

## 2. Golden capture (MATLAB side)

`mlp_instrument.m` copies the upstream `src/` and, for each function file `NAME.m`, renames the
main function to `NAME__orig` and writes a wrapper `NAME.m` that

1. decides whether to record the call (`mlp_should_record`: the first calls, then calls whose input
   signature — classes and sizes — is new, up to a maximum per function),
2. snapshots the inputs *before* the call (handle objects such as `bmSparseMat` may be mutated),
3. forwards to `NAME__orig` with the caller's `nargout`,
4. saves inputs, outputs, `nargin`, `nargout`, caller and upstream commit to a `-v7` MAT-file
   (`mlp_record`); objects are converted to structs with a `mlpClass` field (`mlp_to_plain`).

Recursive and nested calls are recorded too, so one scenario produces fixtures for every function
it reaches. Scenarios (`tools/matlab_capture/scenarios/scenario_*.m`) run the demo pipelines
without display and with interactive steps replaced by fixed choices:

| Scenario | Data | Covers |
|---|---|---|
| `static2d` | demo datasets 1–3 (2D radial, simulated and measured) | volume elements, resize, gridded recon (`bmMathilda`) |
| `tutorial_coilsense` | tutorial 1 body + surface coil raw data (3D radial phyllotaxis, 42 ch) | Siemens reader, trajectory, sparse gridding, coil sensitivity, 3D `bmMathilda` |

Run: `matlab -batch "addpath('tools/matlab_capture'); run_capture('<scenario>', fullfile(pwd,'fixtures','matlab'), '<monalisa root>')"`.

## 3. Port

Each function is translated following [CONVENTIONS.md](../CONVENTIONS.md): same name, arguments,
shapes (column-major) and precision; MEX kernels become numba functions with the same loop order.
The translation can be written by hand or by a coding agent; in both cases the context is the
MATLAB source, its callees' ports, the conventions, and the recorded calls.

## 4. Verify

- **Replay** (`tests/parity/test_matlab_parity.py`): every recording is loaded, converted to the
  Python conventions (`monalisa.testing.from_matlab`), replayed against the ported function and
  compared output by output (`monalisa.testing.compare`): sizes and precision class must match,
  integers/logicals exactly, floating point within the tolerances of `tests/parity/tolerances.py`
  (relative L2 error and maximum error relative to the reference maximum). The replay also fails
  if the function modified one of its inputs in place.
- **Unit and property tests** (`tests/unit`) cover what recordings cannot: e.g. adjointness of
  the forward/adjoint operator pairs, behaviour on edge cases.

## 5. Report

`tools/port_status.py <monalisa root>` replays all recordings and writes `PORTING_STATUS.md`:
per function, whether it is ported, the number of recordings, pass/fail and the worst relative L2
error.

## 6. Sync with upstream

The upstream commit is pinned (`monalisa.UPSTREAM_COMMIT`, stored in every recording). When
upstream changes: re-run the scenarios on the new commit, compare the new recordings with the old
ones, and re-port the functions whose source or recorded behaviour changed.

## Findings worth knowing (MATLAB vs NumPy)

- MATLAB evaluates `single op double` in double and rounds to single; NumPy casts first. NumPy 2
  also promotes `float32 * np.float64` to float64. See `_mat.mixed`.
- `scipy.io.loadmat(mat_dtype=True)` drops the imaginary part of complex arrays, while
  `mat_dtype=False` returns integer storage types for integer-valued doubles; the fixture loader
  reads both and merges them.
- MATLAB `interpn(..., 'cubic')` on uniform grids is Keys cubic convolution (a = −0.5) with Keys'
  boundary extrapolation, reproduced to 6e-8 in `bmImResize`.
- Some upstream MEX files are compiled with `-Ofast`: the Laplace kernels divide by 7 (or 5, 3) as a
  multiplication by the float reciprocal; reproducing it brings the 1000-iteration Laplace solver
  within 1e-5 of MATLAB.
- Single-precision inner products over ~1e5 terms differ by ~1e-5 between MKL (MATLAB) and OpenBLAS
  (NumPy) because of the summation order; this is the only tolerance relaxation of the solvers'
  building blocks (`bmEuclideProd`), and the solver outputs themselves match at 1e-5.
- MATLAB handle objects (`bmWitnessInfo`, `bmSparseMat`, readers) are mutable by design; the replay
  skips them in its input-mutation check. Iterative solvers write witness files to the working
  directory, so every replay runs in a temporary directory.
- `fitgmdist` (random k-means++ start) is replaced by a deterministic EM; thresholds are rounded to
  integers upstream, so the automatic coil-sensitivity mask is identical.
- MATLAB's `imregdemons` (demons registration, Image Processing Toolbox) is replaced by SimpleITK's
  `DemonsRegistrationFilter` (same Thirion update, thresholds and field smoothing) inside a
  reproduction of MATLAB's multiresolution pyramid (`monalisa.imReg._demons`). The pyramid and
  the final warp match MATLAB exactly; ITK's iterations differ in border handling and Gaussian
  kernel, so the fields are validated on quality: [validation_registration.md](validation_registration.md).
- numba 0.68: calling a `parallel=True` kernel from inside another `@njit` function crashed
  (segmentation fault) unless the inner kernel had been compiled on its own first. Loops that call
  parallel kernels are therefore plain Python (`laplace_solve`).
- Speed on large 3D problems is limited by memory copies, not by the FFTs: shifting all axes at
  once around the 1-D FFTs, a complex sparse product without real/imaginary copies, and `mixed`
  computing in double by chunks (no full-size double temporaries) gave 2.3× (Sensa) and 1.4×
  (TevaMorphosia) with bit-identical results. Keeping the arrays in column order in memory (as
  MATLAB does, see CONVENTIONS.md) then removed the copies made by every MATLAB-order reshape and
  `x(:)` of row-major arrays; with parallel `fftshift` copies (`monalisa._fft`), sparse products
  looping one channel at a time, and output arrays cleared by all threads before use (on huge
  pages, threads writing the columns of a fresh array together wait on the same page faults),
  tutorial 1 went from 36:16 to 22:33 (iterative reconstructions 30:49 → 18:26, gridded
  reconstructions 1:12 → 0:30; 36-thread machine). Sums now run in column order, so results
  moved by float32 rounding (relative 1e-7 to 3e-7 from the previous Python run); the
  differences from MATLAB are unchanged (`tests/e2e` report).

## Validation status (tutorial 1)

| Stage | MATLAB → Python |
|---|---|
| Recorded function calls (all scenarios) | see `PORTING_STATUS.md` |
| Binning masks | identical |
| Coil sensitivity, normalization, gridded reconstructions | `tests/e2e/test_tutorial_1.py` report |
| Gridded reconstructions `x0`, `x1` (80³, 42 coils) | rel L2 ≈ 4e-5 |
| Iterative SENSE `bmSensa`, 8 bins × 30 iterations | rel L2 6–8e-5 |
| Compressed sensing `bmTevaMorphosia_chain`, 8 bins × 30 iterations | rel L2 6e-5 |

MATLAB references of the iterative reconstructions: `tools/matlab_capture/validation/tutorial_1_iterative_reference.m`
(from the MATLAB outputs of `scenario_tutorial_recon`).

