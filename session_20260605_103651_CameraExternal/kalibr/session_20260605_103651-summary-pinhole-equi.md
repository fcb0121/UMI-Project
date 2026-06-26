# Kalibr camera-IMU calibration summary

## Camera intrinsics source

- Intrinsics session: `/home/zzzjt/projects/session_20260604_171453`
- Bag: `/home/zzzjt/projects/session_20260604_171453/kalibr/session_20260604_171453.bag`
- Model: `pinhole-equi`
- Output camchain: `/home/zzzjt/projects/session_20260604_171453/kalibr/session_20260604_171453-camchain.yaml`
- Copied camchain used for IMU-camera calibration: `kalibr/camchain_171453_kalibr_pinhole_equi.yaml`
- Camera reprojection error from intrinsics calibration: `[-0.000016, 0.000002] +- [0.343365, 0.369069] px`

Camera intrinsics:

```yaml
camera_model: pinhole
distortion_model: equidistant
intrinsics: [407.16556289023475, 406.5719721278056, 830.9049270734243, 618.1957669770426]
distortion_coeffs: [-0.011925575149450052, -0.003951306310202171, 0.0004051865456881907, -0.00030239381530415495]
resolution: [1640, 1232]
rostopic: /cam0/image_raw
```

## IMU-camera calibration

- IMU-camera session: `/home/zzzjt/projects/session_20260605_103651`
- Bag: `kalibr/session_20260605_103651.bag`
- Camera topic: `/cam0/image_raw`
- IMU topic: `/imu0`
- IMU config: `kalibr/imu_atk_imu601_approx.yaml`
- Target: `kalibr/aprilgrid_6x6_34p5mm.yaml`
- New output camchain: `kalibr/session_20260605_103651-camchain-imucam.yaml`
- New report: `kalibr/session_20260605_103651-report-imucam.pdf`
- Previous approximate-intrinsics output backup: `kalibr/results_approx_intrinsics/`

Final residuals after optimization:

```text
Reprojection error (cam0) [px]:     mean 0.511881859365056, median 0.3839841906618373, std 0.524772409596056
Gyroscope error (imu0) [rad/s]:     mean 0.08135135664057781, median 0.04395298132940742, std 0.3996353712018201
Accelerometer error (imu0) [m/s^2]: mean 0.2671213246917908, median 0.1544986295215391, std 0.6198777185199269
```

Transformation `T_cam0_imu0` / `T_ci` (imu0 to cam0):

```text
[[ 0.99995919 -0.00712909 -0.00554850  0.03112438]
 [-0.00569336 -0.02046306 -0.99977440  0.10244657]
 [ 0.00701395  0.99976519 -0.02050282  0.03072951]
 [ 0.          0.          0.          1.        ]]
```

Transformation `T_ic` (cam0 to imu0):

```text
[[ 0.99995919 -0.00569336  0.00701395 -0.03075538]
 [-0.00712909 -0.02046306  0.99976519 -0.02840403]
 [-0.00554850 -0.99977440 -0.02050282  0.10322620]
 [ 0.          0.          0.          1.        ]]
```

Time offset:

```text
t_imu = t_cam + 0.10594867294770188 s
```

Compared with the previous approximate-intrinsics run, the reprojection mean improved from about `8.1365 px` to `0.5119 px`.
