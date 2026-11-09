# Porting conventions

These rules make the Python port numerically comparable to MATLAB, function by function. They
apply to the *faithful layer* (`monalisa/<upstream folder>/bmFoo.py`). A more Pythonic API can be
added on top later without changing these modules.

## Files and names

- `src/<path>/bmFoo.m` upstream → `src/monalisa/<path>/bmFoo.py`, defining `bmFoo`. Same name, same
  folder structure (including `m/`, `map_function/...`), so that upstream changes map 1:1.
  Folder names that are Python keywords get a trailing underscore (`mriRecon/class` →
  `mriRecon/class_`).
- Module docstring: `"""Port of src/<path>/bmFoo.m."""`. The function docstring says what it does.
- MEX kernels become numba functions in a private module next to the MATLAB wrapper, e.g.
  `gridding123/mex/_gridder_n2u_leight.py`, keeping the MEX function names.
- Internal imports are explicit: `from monalisa.arrayUtility.bmBlockReshape import bmBlockReshape`.
  Users can write `import monalisa as ml; ml.bmMathilda(...)` (lazy lookup).

## Arguments and outputs

- Same positional order as MATLAB. `varargin` options become keyword arguments with default
  `None`, in the order MATLAB unpacks them (`bmVarargin`).
- MATLAB `[]` passed as an argument is `None`. Functions returning `[]` return `None`.
- Several outputs are returned as a tuple. If MATLAB changes behaviour or cost with `nargout`,
  the Python function takes a keyword `nargout` (e.g. `bmTraj_nLine(t, nargout=4)`) and returns
  exactly that many values (a single value when `nargout == 1`).
- Functions never modify their input arrays (MATLAB passes by value). The replay test checks it.
- Interactive steps (`autoFlag = false`: metadata dialogs, coil-mask thresholds and box) are Qt
  dialogs (`qtpy`, matplotlib canvases) that return the same values as MATLAB, and every one has
  a parameter that skips it. The Qt classes live in private modules (`_metadata_dialog.py`),
  built on first use, so that importing a function never needs a display. The image viewers
  (`bmImage`) are replaced by napari rather than ported line by line.
- Progress messages printed by MATLAB (`disp`) are printed through `monalisa._mat.disp`.

## Arrays

- **Same shapes as MATLAB**, at least 2-D: a MATLAB `1×n` row is a `(1, n)` array, `n×1` is
  `(n, 1)`. Trailing singleton dimensions beyond the second are dropped like MATLAB does
  (`_mat.reshape`, `_mat.msize`).
- **Column-major**: every MATLAB `reshape`, `x(:)` and linear index uses `order="F"`
  (`_mat.reshape`, `_mat.col`, `_mat.row`). Never call `np.reshape` without `order="F"` on data
  whose layout matters.
- **Column order in memory too**, as in MATLAB: arrays created by the port are Fortran-ordered
  (`order="F"`, `_mat.repmat` instead of `np.tile`, `.T` copies made with `np.asfortranarray`), so
  the reshapes and `x(:)` above are views, not copies, and NumPy sums go through the elements in
  MATLAB's order. Element-wise NumPy operations keep the order of their inputs; `_mat.mixed`
  returns column order. Numba kernels loop with the first index innermost (or, like the MEX, over
  the contiguous channels of `[nCh, nPt]` arrays). Arrays in the other order are still read
  correctly, only more slowly; element-wise results do not depend on the layout, sums may differ
  in the last bits.
- Indices are 0-based internally. Index *values* returned to the caller keep MATLAB semantics
  (1-based, as doubles) when MATLAB returns them, and this is stated in the docstring.
- Cell arrays are object ndarrays with the MATLAB shape (`_mat.cell_from_items`); lists are
  accepted as input and read as column cells (`_mat.cell_items`, `_mat.cell_shape`).
- Structs are `monalisa._mat.Struct` (dict with attribute access).

## Precision

- `single` → `float32` / `complex64`, `double` → `float64` / `complex128`, `logical` → `bool`,
  `int32` → `int32`. The precision of every output must match MATLAB (the parity test checks it).
- **NumPy 2 promotion differs from MATLAB.** `float32_array * np.float64(x)` gives float64 in
  NumPy but single in MATLAB. Use Python floats or `np.float32(...)` for scalars, or `_mat.mixed`.
- **MATLAB computes `single op double` in double and rounds to single** (measured on R2024b:
  100 % agreement, against 75 % for cast-first). `_mat.mixed(op, a, b)` reproduces it; use it
  where the last bit matters (e.g. trajectory scaling before gridding).
- MATLAB `int32(x)` rounds half away from zero (`_mat.int32`), unlike `np.round`.
- Sorting uses `kind="stable"` (MATLAB `sort` is stable).
- FFTs use `scipy.fft` (keeps single precision); centered transforms are
  `fftshift(fft(ifftshift(x, n), [], n), n)` per axis, exactly as upstream.
- MEX kernels are ported with the same loop order and float32 arithmetic; numba is used without
  `fastmath` so that no FMA contraction happens.

## Validation

- Each port is validated by replaying MATLAB golden recordings (`tests/parity`), see
  `docs/porting_method.md`. Default tolerances: single precision relative L2 ≤ 1e-5 and
  max abs error ≤ 1e-4·max|ref|; double precision 1e-10 / 1e-8; integers and logicals exact.
- Any looser tolerance or expected divergence goes in `tests/parity/tolerances.py` **with the
  reason**.
- Upstream bugs are reproduced, not fixed, and listed in `docs/upstream_issues.md`.
