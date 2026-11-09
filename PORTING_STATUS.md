# Porting status

Generated 2026-11-09 by `tools/port_status.py` against upstream commit `0cb5cf9`.

- Scope: **175 functions** of `src/` reachable from the demo pipelines (11188 code lines).
- Ported: **139** (6989 code lines, 62 %).
- Validated against MATLAB recordings: **109**.

*rel L2* is the worst relative L2 error over all recorded calls and outputs.

| Function | Upstream file | Code lines | Ported | MATLAB parity | worst rel L2 |
|---|---|---:|:---:|---|---:|
| `bmIDF` | src/fourierN/bmIDF.m | 165 | yes | 5/5 ok | 9.7e-08 |
| `bmMriAcquisitionParam` | src/mriRecon/class/bmMriAcquisitionParam.m | 62 | yes | no recording |  |
| `checkMetadataInteractive` | src/rawDataReader/checkMetadataInteractive.m | 163 | yes | no recording |  |
| `dhIsmrmrdReadMetaData` | src/rawDataReader/ismrmrd/dhIsmrmrdReadMetaData.m | 76 | yes | 1/1 ok | 0.0e+00 |
| `dhIsmrmrdReadRawData` | src/rawDataReader/ismrmrd/dhIsmrmrdReadRawData.m | 39 | yes | 2/2 ok | 0.0e+00 |
| `mleRawDataReader` | src/rawDataReader/mleRawDataReader.m | 20 | yes | no recording |  |
| `mleIsmrmrdReader` | src/rawDataReader/ismrmrd/mleIsmrmrdReader.m | 19 | yes | no recording |  |
| `bmSiemensReadRawData` | src/rawDataReader/siemens/bmSiemensReadRawData.m | 34 | yes | 2/2 ok | 0.0e+00 |
| `correctMetadataInteractive` | src/rawDataReader/correctMetadataInteractive.m | 108 | yes | no recording |  |
| `dhSiemensReadMetaData` | src/rawDataReader/siemens/dhSiemensReadMetaData.m | 107 | yes | 4/4 ok | 0.0e+00 |
| `mleSiemensReader` | src/rawDataReader/siemens/mleSiemensReader.m | 19 | yes | no recording |  |
| `createRawDataReader` | src/rawDataReader/createRawDataReader.m | 11 | yes | 6/6 ok | inf |
| `bmAxpy` | src/mathOp/bmAxpy.m | 29 | yes | 6/6 ok | 0.0e+00 |
| `bmBackGradient_n` | src/optim/bmBackGradient_n.m | 33 | yes | 3/3 ok | 0.0e+00 |
| `bmVarargin` | src/varargin/bmVarargin.m | 14 | yes | 29/29 ok | 0.0e+00 |
| `bmZero` | src/arrayUtility/bmZero.m | 22 | yes | 3/3 ok | 0.0e+00 |
| `bmBackGradient` | src/optim/bmBackGradient.m | 8 | yes | 3/3 ok | 0.0e+00 |
| `bmBackGradient_nT` | src/optim/bmBackGradient_nT.m | 34 | yes | 5/5 ok | 0.0e+00 |
| `bmBackGradientT` | src/optim/bmBackGradientT.m | 8 | yes | 4/4 ok | 0.0e+00 |
| `bmBlockReshape` | src/arrayUtility/bmBlockReshape.m | 16 | yes | 28/28 ok | 0.0e+00 |
| `bmCell2Array` | src/arrayUtility/bmCell2Array.m | 24 | yes | no recording |  |
| `bmCheckDir` | src/readWrite/bmCheckDir.m | 16 | yes | 3/3 ok | 0.0e+00 |
| `bmPointReshape` | src/arrayUtility/bmPointReshape.m | 25 | yes | 30/30 ok | 0.0e+00 |
| `bmLowRes` | src/mriRecon/function/bmLowRes.m | 44 | yes | 2/2 ok | 0.0e+00 |
| `bmPermuteToCol` | src/arrayUtility/bmPermuteToCol.m | 24 | yes | 2/2 ok | 0.0e+00 |
| `bmPhyllotaxisAngle3` | src/traj3/bmPhyllotaxisAngle3.m | 31 | yes | 5/5 ok | 0.0e+00 |
| `bmTraj_fullRadial3_phyllotaxis_lineAssym2` | src/traj3/bmTraj_fullRadial3_phyllotaxis_lineAssym2.m | 50 | yes | 5/5 ok | 4.5e-17 |
| `mlTrajFromPulseq` | src/trajN/mlTrajFromPulseq.m | 48 |  |  |  |
| `mlUphyAngle3` | src/traj3/mlUphyAngle3.m | 31 |  |  |  |
| `mlTraj_fullRadial3_phyllotaxis_uniform_lineAssym2` | src/traj3/mlTraj_fullRadial3_phyllotaxis_uniform_lineAssym2.m | 41 |  |  |  |
| `bmTraj` | src/trajN/bmTraj.m | 20 | yes | 4/4 ok | 3.9e-17 |
| `bmTraj_formatTraj` | src/traj123/bmTraj_formatTraj.m | 73 | yes | 3/3 ok | 0.0e+00 |
| `bmTraj_squaredNorm` | src/traj123/bmTraj_squaredNorm.m | 10 | yes | 7/7 ok | 0.0e+00 |
| `bmVolumeElement_cartesian2` | src/geom2/bmVolumeElement_cartesian2.m | 46 | yes | 1/1 ok | 5.9e-16 |
| `bmVolumeElement_cartesian3` | src/geom3/bmVolumeElement_cartesian3.m | 87 |  |  |  |
| `bmTraj_lineDirection` | src/traj123/bmTraj_lineDirection.m | 16 | yes | 17/17 ok | 0.0e+00 |
| `bmTraj_nLine` | src/traj123/bmTraj_nLine.m | 62 | yes | 19/19 ok | 0.0e+00 |
| `bmTraj_lineReshape` | src/traj123/bmTraj_lineReshape.m | 14 | yes | 17/17 ok | 0.0e+00 |
| `bmVolumeElement1` | src/geom1/bmVolumeElement1.m | 12 | yes | 22/22 ok | 0.0e+00 |
| `bmVolumeElement_center_out_radial3` | src/geom3/bmVolumeElement_center_out_radial3.m | 48 | yes | 1/1 ok | 1.4e-15 |
| `bmVolumeElement_full_radial3` | src/geom3/bmVolumeElement_full_radial3.m | 26 | yes | 1/1 ok | 2.0e-15 |
| `bmVolumeElement_imDeformField2` | src/geom2/bmVolumeElement_imDeformField2.m | 38 |  |  |  |
| `bmVolumeElement_imDeformField3` | src/geom3/bmVolumeElement_imDeformField3.m | 66 |  |  |  |
| `bmVolumeElement_randomPartialCartesian2_x` | src/geom2/bmVolumeElement_randomPartialCartesian2_x.m | 16 | yes | 1/1 ok | 0.0e+00 |
| `bmVoronoi` | src/geom123/bmVoronoi.m | 34 | yes | 23/23 ok | 3.0e-15 |
| `bmVolumeElement_voronoi_box2` | src/geom2/bmVolumeElement_voronoi_box2.m | 23 | yes | 2/2 ok | 3.3e-17 |
| `bmVolumeElement_randomPartialCartesian3_x` | src/geom3/bmVolumeElement_randomPartialCartesian3_x.m | 18 | yes | 1/1 ok | 5.3e-19 |
| `bmVolumeElement_voronoi_box3` | src/geom3/bmVolumeElement_voronoi_box3.m | 42 |  |  |  |
| `bmTraj_norm` | src/traj123/bmTraj_norm.m | 11 | yes | 12/12 ok | 0.0e+00 |
| `bmVolumeElement_voronoi_center_out_radial2` | src/geom2/bmVolumeElement_voronoi_center_out_radial2.m | 62 | yes | 1/1 ok | 1.2e-15 |
| `bmVolumeElement_voronoi_center_out_radial3` | src/geom3/bmVolumeElement_voronoi_center_out_radial3.m | 124 |  |  |  |
| `bmVolumeElement_voronoi_full_radial2` | src/geom2/bmVolumeElement_voronoi_full_radial2.m | 42 | yes | 11/11 ok | 1.7e-14 |
| `bmCol` | src/arrayUtility/bmCol.m | 3 | yes | 11/11 ok | 0.0e+00 |
| `bmVolumeElement_voronoi_full_radial2_nonUnique` | src/geom2/bmVolumeElement_voronoi_full_radial2_nonUnique.m | 55 |  |  |  |
| `bmVolumeElement_voronoi_full_radial3` | src/geom3/bmVolumeElement_voronoi_full_radial3.m | 101 | yes | 4/4 ok | 1.7e-14 |
| `bmVolumeElement_voronoi_full_radial3_nonUnique` | src/geom3/bmVolumeElement_voronoi_full_radial3_nonUnique.m | 123 |  |  |  |
| `bmVolumeElement` | src/geom123/bmVolumeElement.m | 59 | yes | 18/18 ok | 1.7e-14 |
| `bmCoilSense_nonCart_data` | src/coilSense/nonCart/bmCoilSense_nonCart_data.m | 23 | yes | 3/3 ok | 8.5e-15 |
| `bmImDim` | src/imageN/bmImDim.m | 35 | yes | 6/6 ok | 0.0e+00 |
| `bmImReshape` | src/image123/bmImReshape.m | 21 | yes | 6/6 ok | 0.0e+00 |
| `bmImShiftList_to_image` | src/image123/bmImShiftList_to_image.m | 43 |  |  |  |
| `bmImShiftList_to_structEl` | src/image123/bmImShiftList_to_structEl.m | 7 |  |  |  |
| `bmImDilate` | src/image123/bmImDilate.m | 3 |  |  |  |
| `bmImErode` | src/image123/bmImErode.m | 3 |  |  |  |
| `bmImClose` | src/image123/bmImClose.m | 5 |  |  |  |
| `bmImOpen` | src/image123/bmImOpen.m | 5 |  |  |  |
| `bmGetNum` | src/dialog/bmGetNum.m | 21 |  |  |  |
| `bmImageViewerParam` | src/imDisp/bmImageViewerParam.m | 123 |  |  |  |
| `bmRotation2` | src/linAlg2/bmRotation2.m | 6 |  |  |  |
| `bmImage2` | src/imDisp/bmImage2.m | 326 |  |  |  |
| `bmGetNat` | src/dialog/bmGetNat.m | 25 |  |  |  |
| `bmTheta_phi` | src/geom3/bmTheta_phi.m | 17 |  |  |  |
| `bmPsi_theta_phi` | src/geom3/bmPsi_theta_phi.m | 43 |  |  |  |
| `bmRotation3` | src/linAlg3/bmRotation3.m | 18 |  |  |  |
| `bmImage3` | src/imDisp/bmImage3.m | 651 |  |  |  |
| `bmImage4` | src/imDisp/bmImage4.m | 595 |  |  |  |
| `bmImage5` | src/imDisp/bmImage5.m | 618 |  |  |  |
| `bmImage` | src/imDisp/bmImage.m | 25 | yes | no recording |  |
| `bmImShiftList` | src/image123/bmImShiftList.m | 52 |  |  |  |
| `bmColReshape` | src/arrayUtility/bmColReshape.m | 12 | yes | 20/20 ok | 0.0e+00 |
| `bmIsBlockShape` | src/arrayUtility/bmIsBlockShape.m | 10 | yes | 14/14 ok | 0.0e+00 |
| `bmIsColShape` | src/arrayUtility/bmIsColShape.m | 10 | yes | 12/12 ok | 0.0e+00 |
| `bmMIP` | src/imageN/bmMIP.m | 9 | yes | 2/2 ok | 5.2e-08 |
| `bmCoilSense_pinv` | src/coilSense/map/bmCoilSense_pinv.m | 6 | yes | 10/10 ok | 9.2e-08 |
| `bmIDF1` | src/fourier1/bmIDF1.m | 9 | yes | no recording |  |
| `bmIDF2` | src/fourier2/bmIDF2.m | 11 | yes | 6/6 ok | 1.9e-07 |
| `bmIDF3` | src/fourier3/bmIDF3.m | 13 | yes | 8/8 ok | 2.1e-07 |
| `bmImCrope` | src/image123/bmImCrope.m | 37 | yes | 9/9 ok | 0.0e+00 |
| `bmDFT1` | src/fourier1/bmDFT1.m | 9 | yes | no recording |  |
| `bmDFT2` | src/fourier2/bmDFT2.m | 11 | yes | 9/9 ok | 2.4e-16 |
| `bmDFT3` | src/fourier3/bmDFT3.m | 13 | yes | 7/7 ok | 2.7e-16 |
| `bmVarargin_kernelType_nWin_kernelParam` | src/varargin/bmVarargin_kernelType_nWin_kernelParam.m | 36 | yes | 20/20 ok | 0.0e+00 |
| `bmK` | src/fourier123/prep_function/bmK.m | 126 | yes | 16/16 ok | 0.0e+00 |
| `bmSparseMat_vec` | src/sparseMat/m/bmSparseMat_vec.m | 189 | yes | 13/13 ok | 0.0e+00 |
| `bmNasha` | src/fourier123/map_function/nonCartesian/bmNasha.m | 94 | yes | 5/5 ok | 5.3e-07 |
| `bmRMS` | src/imageN/bmRMS.m | 9 | yes | 4/4 ok | 4.9e-08 |
| `detectROI` | src/coilSense/automatic/detectROI.m | 37 | yes | 4/4 ok | 0.0e+00 |
| `selectROI` | src/coilSense/automatic/selectROI.m | 333 | yes | no recording |  |
| `thresholdRMS_MIP` | src/coilSense/automatic/thresholdRMS_MIP.m | 182 | yes | 2/2 ok | 0.0e+00 |
| `bmCoilSense_nonCart_mask_automatic` | src/coilSense/nonCart/bmCoilSense_nonCart_mask_automatic.m | 84 | yes | 1/1 ok | 0.0e+00 |
| `bmImLaplaceIterator` | src/image123/bmImLaplaceIterator.m | 83 | yes | 6/6 ok | 5.8e-07 |
| `bmImLaplacian` | src/image123/bmImLaplacian.m | 35 | yes | 6/6 ok | 0.0e+00 |
| `bmImLaplaceEquationSolver` | src/image123/bmImLaplaceEquationSolver.m | 14 | yes | 6/6 ok | 2.7e-06 |
| `bmImPseudoDiffusion_inMask` | src/image123/bmImPseudoDiffusion_inMask.m | 46 | yes | 6/6 ok | 9.4e-08 |
| `bmY_ve_reshape` | src/linSpace/bmY_ve_reshape.m | 38 | yes | 11/11 ok | 0.0e+00 |
| `bmY_norm` | src/linSpace/bmY_norm.m | 18 | yes | 2/2 ok | 8.2e-08 |
| `bmCoilSense_nonCart_primary` | src/coilSense/nonCart/bmCoilSense_nonCart_primary.m | 39 | yes | no recording |  |
| `bmCoilSense_nonCart_ref` | src/coilSense/nonCart/bmCoilSense_nonCart_ref.m | 60 | yes | 1/1 ok | 1.4e-06 |
| `bmImPseudoDiffusion` | src/image123/bmImPseudoDiffusion.m | 38 | yes | 4/4 ok | 1.1e-07 |
| `bmKF` | src/fourier123/prep_function/bmKF.m | 21 | yes | 7/7 ok | 0.0e+00 |
| `bmKF_conj` | src/fourier123/prep_function/bmKF_conj.m | 21 | yes | 7/7 ok | 0.0e+00 |
| `bmNakatsha_CUFFT_omp` | src/fourier123/map_function/nonCartesian/bmNakatsha_CUFFT_omp.m | 58 |  |  |  |
| `bmNakatsha_FFTW_omp` | src/fourier123/map_function/nonCartesian/bmNakatsha_FFTW_omp.m | 58 |  |  |  |
| `bmNakatsha_MATLAB` | src/fourier123/map_function/nonCartesian/bmNakatsha_MATLAB.m | 61 | yes | 8/8 ok | 1.9e-07 |
| `bmNakatsha` | src/fourier123/map_function/nonCartesian/bmNakatsha.m | 24 | yes | 8/8 ok | 1.9e-07 |
| `bmShanna_CUFFT_omp` | src/fourier123/map_function/nonCartesian/bmShanna_CUFFT_omp.m | 57 |  |  |  |
| `bmShanna_FFTW_omp` | src/fourier123/map_function/nonCartesian/bmShanna_FFTW_omp.m | 57 |  |  |  |
| `bmImZeroFill` | src/image123/bmImZeroFill.m | 41 | yes | no recording |  |
| `bmShanna_MATLAB` | src/fourier123/map_function/nonCartesian/bmShanna_MATLAB.m | 60 | yes | 4/4 ok | 2.4e-07 |
| `bmShanna` | src/fourier123/map_function/nonCartesian/bmShanna.m | 18 | yes | 4/4 ok | 2.4e-07 |
| `bmCoilSense_nonCart_secondary` | src/coilSense/nonCart/bmCoilSense_nonCart_secondary.m | 60 | yes | no recording |  |
| `bmCreateDir` | src/readWrite/bmCreateDir.m | 19 | yes | 3/3 ok | 0.0e+00 |
| `bmDFT1_conjTrans` | src/fourier1/bmDFT1_conjTrans.m | 9 | yes | no recording |  |
| `bmDFT2_conjTrans` | src/fourier2/bmDFT2_conjTrans.m | 11 | yes | no recording |  |
| `bmDFT3_conjTrans` | src/fourier3/bmDFT3_conjTrans.m | 13 | yes | no recording |  |
| `bmIsScalar` | src/arrayUtility/bmIsScalar.m | 14 | yes | 9/9 ok | 0.0e+00 |
| `bmEuclideProd` | src/mathOp/bmEuclideProd.m | 35 | yes | 10/10 ok | 1.5e-05 |
| `bmGridder_n2u` | src/gridding123/m/bmGridder_n2u.m | 148 |  |  |  |
| `bmGridder_n2u_leight` | src/gridding123/m/bmGridder_n2u_leight.m | 90 | yes | 13/13 ok | 0.0e+00 |
| `bmIDF1_conjTrans` | src/fourier1/bmIDF1_conjTrans.m | 9 | yes | no recording |  |
| `bmIDF2_conjTrans` | src/fourier2/bmIDF2_conjTrans.m | 11 | yes | no recording |  |
| `bmIDF3_conjTrans` | src/fourier3/bmIDF3_conjTrans.m | 13 | yes | no recording |  |
| `bmImDeform` | src/image123/bmImDeform.m | 31 | yes | 3/3 ok | 0.0e+00 |
| `bmSparseMat_r_nJump2index` | src/sparseMat/m/bmSparseMat_r_nJump2index.m | 14 | yes | 10/10 ok | 0.0e+00 |
| `bmImDeformField2sparseMat_ind_weight` | src/gridding123/m/bmImDeformField2sparseMat_ind_weight.m | 111 | yes | 2/2 ok | 3.8e-17 |
| `bmSparseMat_completeMatlabSparse` | src/sparseMat/m/bmSparseMat_completeMatlabSparse.m | 18 | yes | 15/15 ok | inf |
| `bmSparseMat_blockPartition` | src/sparseMat/m/bmSparseMat_blockPartition.m | 105 | yes | 14/14 ok | 0.0e+00 |
| `bmSparseMat` | src/sparseMat/m/bmSparseMat.m | 267 | yes | no recording |  |
| `bmSparseMat_matlabSparse2bmSparseMat` | src/sparseMat/m/bmSparseMat_matlabSparse2bmSparseMat.m | 25 | yes | 10/10 ok | 0.0e+00 |
| `bmImDeformField2SparseMat` | src/gridding123/m/bmImDeformField2SparseMat.m | 103 | yes | 1/1 ok | 0.0e+00 |
| `bmImDeformField_hardThresholding2` | src/image2/m/bmImDeformField_hardThresholding2.m | 20 | yes | 2/2 ok | 0.0e+00 |
| `bmPermuteToPoint` | src/arrayUtility/bmPermuteToPoint.m | 18 | yes | 2/2 ok | 0.0e+00 |
| `bmImDeformFieldChain_imRegDemons23` | src/imReg/m/bmImDeformFieldChain_imRegDemons23.m | 120 | yes | 0/2 ok (2 known div.) |  |
| `bmImDeformFieldSheet_imRegDemons23` | src/imReg/m/bmImDeformFieldSheet_imRegDemons23.m | 141 | yes | no recording |  |
| `bmImDeformT` | src/image123/bmImDeformT.m | 31 | yes | 5/5 ok | 0.0e+00 |
| `bmImResize` | src/image123/bmImResize.m | 91 | yes | 4/4 ok | 6.2e-08 |
| `bmIndex2MultiIndex` | src/arrayUtility/bmIndex2MultiIndex.m | 20 | yes | 2/2 ok | 0.0e+00 |
| `bmInitialWitnessInfo` | src/optim/bmInitialWitnessInfo.m | 34 | yes | 8/8 ok | 0.0e+00 |
| `bmTraj_N_u` | src/traj123/bmTraj_N_u.m | 11 | yes | 3/3 ok | 0.0e+00 |
| `bmTraj_dK_u` | src/traj123/bmTraj_dK_u.m | 60 | yes | 3/3 ok | 0.0e+00 |
| `bmTraj_N_u_dK_u` | src/traj123/bmTraj_N_u_dK_u.m | 22 | yes | 16/16 ok | 0.0e+00 |
| `bmVarargin_N_u_dK_u` | src/varargin/bmVarargin_N_u_dK_u.m | 6 | yes | 16/16 ok | 0.0e+00 |
| `bmMathilda` | src/fourier123/map_function/nonCartesian/bmMathilda.m | 82 | yes | 14/14 ok | 5.4e-07 |
| `bmMinus` | src/mathOp/bmMinus.m | 19 | yes | 7/7 ok | 0.0e+00 |
| `bmMitosis` | src/arrayUtility/bmMitosis.m | 73 | yes | no recording |  |
| `bmMitosius_create` | src/mitosius/bmMitosius_create.m | 40 | yes | no recording |  |
| `bmMitosius_load` | src/mitosius/bmMitosius_load.m | 56 | yes | no recording |  |
| `bmMult` | src/mathOp/bmMult.m | 17 | yes | 5/5 ok | 0.0e+00 |
| `bmPlus` | src/mathOp/bmPlus.m | 13 | yes | 5/5 ok | 0.0e+00 |
| `bmProx_oneNorm` | src/linSpace/bmProx_oneNorm.m | 31 | yes | 4/4 ok | 0.0e+00 |
| `bmSensa` | src/fourier123/solver_function/imDim/nonCartesian/bmSensa.m | 72 | yes | 1/1 ok | 1.2e-06 |
| `bmSingle` | src/arrayUtility/bmSingle.m | 15 | yes | 6/6 ok | 0.0e+00 |
| `bmSquaredNorm` | src/mathOp/bmSquaredNorm.m | 3 | yes | 10/10 ok | 1.5e-05 |
| `bmSensitivaDuoMorphosia_chain` | src/fourier123/solver_function/imDim_morphosia/nonCartesian/bmSensitivaDuoMorphosia_chain.m | 182 |  |  |  |
| `bmSensitivaMorphosia_chain` | src/fourier123/solver_function/imDim_morphosia/nonCartesian/bmSensitivaMorphosia_chain.m | 152 | yes | no recording |  |
| `bmSensitivaMorphosia_sheet` | src/fourier123/solver_function/imDim_morphosia/nonCartesian/bmSensitivaMorphosia_sheet.m | 200 |  |  |  |
| `bmSleva` | src/fourier123/solver_function/imDim/nonCartesian/bmSleva.m | 118 | yes | 1/1 ok | 1.2e-06 |
| `bmSteva` | src/fourier123/solver_function/imDim/nonCartesian/bmSteva.m | 122 | yes | 1/1 ok | 1.7e-06 |
| `bmTevaDuoMorphosia_chain` | src/fourier123/solver_function/imDim_morphosia/nonCartesian/bmTevaDuoMorphosia_chain.m | 217 | yes | no recording |  |
| `bmTevaMorphosia_chain` | src/fourier123/solver_function/imDim_morphosia/nonCartesian/bmTevaMorphosia_chain.m | 165 | yes | no recording |  |
| `bmTevaMorphosia_sheet` | src/fourier123/solver_function/imDim_morphosia/nonCartesian/bmTevaMorphosia_sheet.m | 223 |  |  |  |
| `bmTimeInSecond` | src/time/bmTimeInSecond.m | 4 | yes | 4/4 ok | 0.0e+00 |
| `bmVarargin_sparseType` | src/varargin/bmVarargin_sparseType.m | 7 | yes | 6/6 ok | 0.0e+00 |
| `bmTraj2SparseMat` | src/gridding123/m/bmTraj2SparseMat.m | 255 | yes | 7/7 ok | 0.0e+00 |
| `bmWitnessInfo` | src/optim/bmWitnessInfo.m | 138 | yes | no recording |  |
