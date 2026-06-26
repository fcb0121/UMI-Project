# VIO tuning report

Dataset: `session_20260610_112528`

## What was tested

1. CSV IMU input with the existing `T_b_c1` and noisy IMU parameters.
2. Lower/tighter IMU noise parameters from the earlier nominal calibration scale.
3. Inverted `T_b_c1` to test whether the extrinsic direction was reversed.
4. Raw CSV + noisy parameters, but skip VIBA2 and periodic scale refinement after the first inertial initialization.

## Results

| run | valid poses | PCA ranges | closure/path | IMU init behavior |
| --- | ---: | --- | ---: | --- |
| visual IMU-mode, no init `raspi_backendfix_full` | 1975/2195 | 0.161, 0.072, 0.029 | 0.00060 | no inertial init |
| raw CSV noisy `raspi_backendfix_imu_csv_raw_full` | 1975/2195 | 1.744, 1.164, 0.106 | 0.00915 | VIBA1 and VIBA2 started |
| raw CSV noisy skip VIBA2 `raspi_vio_noisy_skipviba2_full` | 1975/2195 | 1.386, 0.856, 0.133 | 0.00806 | VIBA1 started, VIBA2 skipped |
| tuned low-noise `raspi_vio_tuned_full` | 1975/2195 | 0.161, 0.059, 0.029 | 0.00008 | did not initialize; repeated insufficient excitation |
| tuned low-noise + inverted extrinsic `raspi_vio_tuned_Tinv_full` | 1130/2195 | 0.202, 0.080, 0.023 | 0.00457 | frequent resets, worse tracking |

## Interpretation

- The IMU can be connected back through CSV input. The raw CSV noisy run successfully triggers ORB-SLAM3 inertial initialization and VIBA.
- Inverting `T_b_c1` is clearly worse. It causes resets and loses the first half of the sequence, so the original extrinsic direction is the better direction for ORB-SLAM3.
- The lower/tighter noise parameters are too optimistic for this current pipeline. They make the pre-init visual/inertial state shrink so much that the excitation gate is not passed.
- Skipping VIBA2 improves closure slightly versus full raw CSV noisy, but not dramatically. The main useful setting is still raw CSV + original extrinsic + robust/noisy IMU parameters.

## Current recommended VIO baseline

Use:

```bash
RASPI_ORBSLAM3_ENABLE_IMU_INIT=1 RASPI_ORBSLAM3_SKIP_VIBA2=1 RASPI_ORBSLAM3_SKIP_SCALE_REFINEMENT=1 ./Examples/Monocular-Inertial/raspi_mono_inertial_slam   -v Vocabulary/ORBvoc.txt   -s /workspace/session_20260610_112528/orbslam3_output/raspi_imx219_mono_inertial_noisy_820x616.yaml   -i /workspace/session_20260610_112528/raw_video.mp4   --input_imu_csv /workspace/session_20260610_112528/imu_data.csv   --frame_timestamps_csv /workspace/session_20260610_112528/video_timestamps.csv
```

Useful outputs:

- `orbslam3_output/raspi_vio_noisy_skipviba2_full_map_plus_trajectory_color.ply`
- `orbslam3_output/raspi_vio_noisy_skipviba2_full_trajectory_pca.svg`
- `orbslam3_output/raspi_backendfix_imu_csv_raw_full_map_plus_trajectory_color.ply`
- `orbslam3_output/raspi_backendfix_imu_csv_raw_full_trajectory_pca.svg`

## Next tuning target

The system now initializes IMU, but VIO is not yet final. The next likely improvements are:

1. Keep original `T_b_c1`, do not invert it.
2. Use CSV IMU input, not JSON.
3. Keep robust/noisy IMU parameters for this hardware path unless a proper Allan variance calibration is available.
4. Tune initialization window/excitation gates and VIBA2 behavior on more datasets, because VIBA2 currently does not improve this sequence much.
