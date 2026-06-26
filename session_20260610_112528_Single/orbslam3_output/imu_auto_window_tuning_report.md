# IMU auto initialization window report

Dataset: `session_20260610_112528`

Input mode: CSV IMU + original `T_b_c1`

Backend setting: auto first IMU init window, `RASPI_ORBSLAM3_SKIP_VIBA2=1`, `RASPI_ORBSLAM3_SKIP_SCALE_REFINEMENT=1`

## Code change

`LocalMapping.cc` no longer uses only a fixed first-init time/KF gate for monocular inertial initialization. It now scans recent temporal keyframe windows and accepts the first-init window only when the visual motion has enough:

- IMU preintegration edges
- accumulated visual path
- start-to-window baseline
- accumulated rotation
- bounded per-step translation

The old fixed gate can still be restored with:

`RASPI_ORBSLAM3_IMU_AUTO_WINDOW_DISABLE=1`

Main tunable defaults:

- `RASPI_ORBSLAM3_IMU_AUTO_MIN_KFS=15`
- `RASPI_ORBSLAM3_IMU_AUTO_MIN_EDGES=12`
- `RASPI_ORBSLAM3_IMU_AUTO_MIN_PATH=0.05`
- `RASPI_ORBSLAM3_IMU_AUTO_MIN_BASELINE=0.015`
- `RASPI_ORBSLAM3_IMU_AUTO_MIN_ROT_DEG=55`
- `RASPI_ORBSLAM3_IMU_AUTO_MAX_WINDOW=12`
- `RASPI_ORBSLAM3_IMU_AUTO_MAX_STEP=0.25`

## Results

| case | selected init | valid/rows | KFs | path | end error | closure/path | PCA ranges |
|---|---|---:|---:|---:|---:|---:|---|
| `raspi_vio_noisy_skipviba2_full` | old fixed-ish baseline | 1975/2195 | 73 | 12.699 | 0.102 | 0.00806 | 1.386, 0.856, 0.133 |
| `raspi_vio_early_relaxed_skipviba2_full` | manual 5s/15KF relaxed gate | 1975/2195 | 68 | 8.539 | 0.055 | 0.00639 | 0.803, 0.627, 0.125 |
| `raspi_vio_autowindow_skipviba2_full` | auto: KF 1 to 18, 4.53s, 18 KFs, 17 IMU edges, path 0.135, baseline 0.112, rotation 58.2 deg | 1975/2195 | 71 | 11.836 | 0.111 | 0.00941 | 1.376, 0.917, 0.107 |
| `raspi_vio_autowindow_rot70_skipviba2_full` | auto with `AUTO_MIN_ROT_DEG=70`: 5.87s, 21 KFs, rotation 74.1 deg | 1975/2195 | 71 | 15.774 | 0.149 | 0.00944 | 1.804, 1.198, 0.135 |

## Interpretation

The automatic window logic is working: it waits for a real visual motion window and logs the accepted baseline/rotation/path instead of blindly using elapsed time. The default 55 degree rotation gate gives the flattest trajectory among the automatic variants, with PCA thickness `0.107`.

The manual 5s/15KF relaxed run still has the best closure ratio on this dataset, but it depends on hand-picked fixed timing. The automatic window is a better backend behavior for future captures because it will adapt to the actual visual motion and reject weak early windows.

## Current recommendation

Use `raspi_vio_autowindow_skipviba2_full` as the automatic-window baseline, and keep VIBA2/scale refinement disabled for now. If the next capture has stronger smooth motion around the table, this auto gate should pick a reasonable first inertial initialization point without retuning fixed seconds.
