# Validation: demons registration and motion-compensated reconstructions

MATLAB's `imregdemons` (Image Processing Toolbox) is replaced by an open-source implementation,
`monalisa.registration._demons.imregdemons`, so that the registration wrappers
`im_deform_field_chain_im_reg_demons23` and `im_deform_field_sheet_im_reg_demons23` (MATLAB
`bmImDeformFieldChain_imRegDemons23`, `bmImDeformFieldSheet_imRegDemons23`) need no MATLAB
licence.

## Implementation

- **Iterations:** SimpleITK's `DemonsRegistrationFilter`. It uses the same Thirion update as
  MATLAB, `(F − M∘D) ∇F / (|∇F|² + (F − M∘D)²)`, with the same thresholds (0.001 and 1e-9) and the
  same Gaussian smoothing of the accumulated field (σ = 1 pixel). It always runs all the requested
  iterations (no RMS stopping criterion).
- **Pyramid** (reproduced from MATLAB's `MultiResolutionDemons2D/3D`):
  - images padded by replication to a multiple of 2^(levels−1);
  - images downsampled at each level, in 2D with antialiased bicubic `imresize`, in 3D with a
    Butterworth low-pass followed by linear resampling;
  - the field upsampled ×2 between levels and its displacements multiplied by 2;
  - the first element of `iterations` applies to the coarsest level.

  These steps match MATLAB to rounding (2D resize and 3D resampling: ≤ 2e-16).
- **Final warp:** `moving(p + D(p))` with linear interpolation, blending to zero outside the image
  (MATLAB's `imwarp(..., 'SmoothEdges', true)`), equal to MATLAB to 2e-8.

The remaining difference is inside ITK's iterations: image gradient at the borders, discrete
Gaussian kernel, and the rule for warped samples outside the image. The fields are therefore
compared on quality, not to rounding. As a check of everything around the iterations, replacing
ITK's iteration by a direct transcription of MATLAB's reproduces `imregdemons` to 1e-14, and the
wrappers' outputs to 2e-4 (single precision).

## Results

Run with `MONALISA_UPSTREAM=/path/to/monalisa pytest tests/validation -s`; MATLAB references from
`tools/matlab_capture/validation/imregdemons_reference.m` and `registration_reference.m`.

### imregdemons on synthetic images with known deformations

Field difference to MATLAB where the image has structure (gradient > 5 % of max). Image error is
the relative L2 error of the registered image vs the fixed image, away from the borders.

| Case | Levels | Field EPE mean / p95 (px) | Mean MATLAB displacement (px) | Image error before | MATLAB | Python |
|---|---|---|---|---|---|---|
| phantom 2D 128² | 3 | 0.13 / 0.41 | 1.57 | 0.508 | 0.048 | 0.034 |
| phantom 2D 128² | 1 | 0.10 / 0.39 | 1.28 | 0.508 | 0.048 | 0.034 |
| texture 2D 100×90 | 3 | 0.15 / 0.53 | 3.63 | 0.217 | 0.053 | 0.066 |
| ellipsoids 3D 48³ | 3 | 0.50 / 0.85 | 1.81 | 0.342 | 0.013 | 0.003 |
| ellipsoids 3D 48³ | 1 | 0.08 / 0.19 | 1.27 | 0.342 | 0.017 | 0.005 |

### Demo chain reconstructions (demo data 5, 14 frames 256², parameters of `chain_recon_calls_script.m`)

Pipeline: Mathilda → TevaMorphosia_chain (no deformation) → demons fields (500 iterations,
`reg_mask`, max 10 px) → motion-compensated reconstructions (30 iterations).

| Stage | Python vs MATLAB |
|---|---|
| Mathilda `x0` | rel L2 < 1e-6 |
| TevaMorphosia_chain without fields `x1` | rel L2 1e-5, SSIM 1.0 |
| Demons fields `curr_to_prev` (same input `x1`), inside `reg_mask` | EPE mean 0.39 px, p95 0.70 px (MATLAB displacement mean 1.57 px) |
| Registered images | rel L2 0.028, SSIM 0.993 |
| TevaMorphosia / TevaDuoMorphosia / SensitivaMorphosia **with MATLAB's fields** | rel L2 1e-5 / 1e-5 / < 1e-5 (solvers validated end to end) |
| … **with the Python fields** | rel L2 0.055 / 0.044 / 0.055, SSIM 0.976 / 0.983 / 0.985 |
| For scale: effect of motion compensation itself (with vs without fields, MATLAB) | rel L2 0.092 / 0.092 / 0.104, SSIM 0.943 / 0.941 / 0.952 |

### Demo sheet registration (demo data 7, 6×4 Mathilda reconstructions 192², 100 iterations)

| Field | EPE mean / p95 (px) | MATLAB displacement mean (px) |
|---|---|---|
| along dimension 1 | 0.90 / 3.3 | 3.28 |
| along dimension 2 | 1.09 / 4.4 | 5.84 |

These undersampled single-bin reconstructions are noisy, and the registration is sensitive to small
algorithmic differences in MATLAB itself: on some cells the registered image is further from the
target than the unregistered one.

## Interpretation

On clean images the SimpleITK demons register as well as MATLAB's (equal or lower image error in
four of five cases, slightly higher on the texture). Their fields differ by a fraction of a pixel.
In the demo chain, the reconstruction obtained with the Python fields differs from MATLAB's by
about half of the change that motion compensation itself makes. That is a different but
equivalent registration, not a numerical reproduction. Studies comparing results with the MATLAB
version should expect this level of difference in motion-compensated reconstructions.
Reconstructions without registration, and the solvers given the same fields, match MATLAB at
single-precision level.
