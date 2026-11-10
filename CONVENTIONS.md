# Porting conventions

These rules make the Python port numerically comparable to MATLAB, function by function, while
the names and the package layout follow Python conventions.

## Files and names

- **Names** follow [PEP 8](https://peps.python.org/pep-0008/#naming-conventions) without the
  authors' initials of the upstream names (`bm`, `mle`, `dh`): functions and methods in
  `snake_case`, classes in `CapWords`, a `2` between words read as *to*
  (`bmCoilSense_nonCart_data` → `coil_sense_non_cart_data`, `bmTraj2SparseMat` →
  `traj_to_sparse_mat`, `mleSiemensReader` → `SiemensReader`). The rule is
  `tools/renaming_table.py:python_name`; a name that departs from it (typo, one-letter name,
  `N_u`/`n_u` lost in lower case) needs a reason in `REASONS` there. The reconstruction methods
  keep their Monalisa names (`mathilda`, `sensa`, `teva_morphosia_chain`).
- **Subpackages by topic** (`monalisa.recon`, `monalisa.io`, `monalisa.fourier`, ...; list in
  README.md). Each function or class has its own private module named after it:
  `src/<path>/bmFoo.m` upstream → `src/monalisa/<subpackage>/_foo.py` defining `foo`. The
  subpackage `__init__.py` imports it and lists it in `__all__`; the top-level package re-exports
  all of them (`import monalisa as ml; ml.mathilda(...)`).
- **The link to upstream** is `monalisa.MATLAB_NAMES` (`src/monalisa/_upstream.py`):
  `"bmFoo": "subpackage.foo"` for every ported function. The MATLAB recordings are stored and
  replayed under the MATLAB names through it, and `docs/renaming.md` is generated from it
  (`python tools/renaming_table.py`). A new port adds its line there and its import to the
  subpackage and top-level `__init__.py`; `tests/unit/test_api.py` checks that the three agree,
  that the names follow the rule and that the table is up to date.
- Module docstring: `"""Port of src/<path>/bmFoo.m."""` (the upstream file, used for the table).
  The function docstring says what it does. No authorship in the source files: authors are
  credited in README.md and recorded in the git history.
- MEX kernels become numba functions in a private module next to their wrapper, e.g.
  `gridding/_gridder_kernels.py`.
- Internal imports go to the private modules, never to a subpackage
  (`from monalisa.array._block_reshape import block_reshape`), so that the subpackages can import
  each other in any order.

## Arguments and outputs

- Argument names, struct fields and object properties keep their MATLAB names (`N_u`, `dK_u`,
  `nCh`, `acquisitionParams.nShot_off`): they are the notation of the Monalisa papers, `N_u`
  (grid size) and `n_u` (image size) are different quantities, and fields are compared with the
  MATLAB recordings. String option values keep the MATLAB values too (`sparseType='bmSparseMat'`).
- Same positional order as MATLAB. `varargin` options become keyword arguments with default
  `None`, in the order MATLAB unpacks them (`util.varargin`).
- MATLAB `[]` passed as an argument is `None`. Functions returning `[]` return `None`.
- Several outputs are returned as a tuple. If MATLAB changes behaviour or cost with `nargout`,
  the Python function takes a keyword `nargout` (e.g. `traj_n_line(t, nargout=4)`) and returns
  exactly that many values (a single value when `nargout == 1`).
- Functions never modify their input arrays (MATLAB passes by value). The replay test checks it.
- Interactive steps (`autoFlag = false`: metadata dialogs, coil-mask thresholds and box) are Qt
  dialogs (`qtpy`, matplotlib canvases) that return the same values as MATLAB, and every one has
  a parameter that skips it. The Qt classes live in private modules (`_metadata_dialog.py`),
  built on first use, so that importing a function never needs a display. The image viewers
  (`bmImage`) are replaced by napari (`show_image`) rather than ported line by line.
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
